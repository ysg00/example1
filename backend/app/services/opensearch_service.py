import os
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError
import boto3
import io
import uuid
from typing import List, Dict, Any
from datetime import datetime
from langchain_core.documents.base import Blob
from langchain_community.document_loaders.parsers import PyMuPDFParser
from sentence_transformers import SentenceTransformer

class OpenSearchService:
    def __init__(self):
        self.client = OpenSearch(
            hosts=[{'host': os.getenv('OPENSEARCH_HOST', 'localhost'), 'port': int(os.getenv('OPENSEARCH_PORT', 9200))}],
            http_auth=(os.getenv('OPENSEARCH_USER', 'admin'), os.getenv('OPENSEARCH_PASSWORD', 'admin')),
            use_ssl=os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true',
            verify_certs=False,
            ssl_show_warn=False,
            http_compress=True
        )
        self.index_name = os.getenv('OPENSEARCH_INDEX', 'pdf_vectors')
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'pdf-storage-bucket')
        
        # Initialize sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create index if it doesn't exist
        self._create_index_if_not_exists()
    
    def _create_index_if_not_exists(self):
        """Create the vector index if it doesn't exist"""
        try:
            if self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
            
            index_body = {
                "settings": {
                    "index": {
                        "knn": True
                    }
                },
                "mappings": {
                    "properties": {
                        "pdf_id": {"type": "integer"},
                        "filename": {"type": "text"},
                        "text": {"type": "text"},
                        "title": {"type": "text"},
                        "author": {"type": "keyword"},
                        "vector": {
                            "type": "knn_vector",
                            "dimension": 384,  # all-MiniLM-L6-v2 dimension
                            "method": {
                                "name": "hnsw",
                                "engine": "lucene",
                                "space_type": "cosinesimil",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 16
                                }
                            }
                        }
                    }
                }
            }
            self.client.indices.create(index=self.index_name, body=index_body)
        except Exception as e:
            print(f"Error creating index: {e}")
    
    def download_pdf_from_s3(self, s3_key: str) -> bytes:
        """Download PDF from S3 and return as bytes"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            raise Exception(f"Error downloading PDF from S3: {str(e)}")
    
    def parse_pdf_content(self, pdf_bytes: bytes) -> List[str]:
        """Parse PDF content using PyMuPDF parser"""
        try:
            # Create a temporary file-like object
            pdf_io = io.BytesIO(pdf_bytes)
            
            # Create blob from bytes
            blob = Blob(data=pdf_bytes, mime_type="application/pdf")
            
            # Parse PDF using PyMuPDF
            parser = PyMuPDFParser(
                mode="single",
                pages_delimiter=""
            )
            
            docs = []
            docs_lazy = parser.lazy_parse(blob)
            
            for doc in docs_lazy:
                docs.append(doc)
            
            # Extract text and split into sentences
            texts = []
            for doc in docs:
                for line in doc.page_content.split('.'):
                    if line.strip():  # Only add non-empty lines
                        texts.append(line.strip())
            
            return texts
            
        except Exception as e:
            raise Exception(f"Error parsing PDF content: {str(e)}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text content using sentence transformers"""
        try:
            vectors = self.model.encode(texts, convert_to_numpy=True)
            return vectors.tolist()
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")
    
    def analyze_and_index_pdf(self, pdf_id: int, filename: str, s3_key: str) -> str:
        """Analyze PDF and store in vector database"""
        try:
            # Download PDF from S3
            pdf_bytes = self.download_pdf_from_s3(s3_key)
            
            # Parse PDF content
            texts = self.parse_pdf_content(pdf_bytes)
            
            # Generate embeddings
            vectors = self.generate_embeddings(texts)
            
            # Index each text segment with its vector
            for i, (text, vector) in enumerate(zip(texts, vectors)):
                doc = {
                    "pdf_id": pdf_id,
                    "filename": filename,
                    "text": text,
                    "vector": vector,
                    "title": f"{filename}_segment_{i}",
                    "author": f"pdf_{pdf_id}"
                }
                
                # Use a unique ID for each segment
                segment_id = f"{pdf_id}_{i}"
                self.client.index(index=self.index_name, id=segment_id, body=doc)
            
            # Return a reference ID for the PDF
            vector_index_id = f"pdf_{pdf_id}"
            return vector_index_id
            
        except Exception as e:
            raise Exception(f"Error analyzing and indexing PDF: {str(e)}")
    
    def delete_pdf_from_index(self, vector_index_id: str) -> bool:
        """Delete PDF from vector index"""
        try:
            # Delete all segments for this PDF
            search_body = {
                "query": {
                    "term": {
                        "pdf_id": int(vector_index_id.replace("pdf_", ""))
                    }
                }
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            for hit in response['hits']['hits']:
                self.client.delete(index=self.index_name, id=hit['_id'])
            
            return True
        except NotFoundError:
            return True  # Already deleted
        except Exception as e:
            raise Exception(f"Error deleting from vector index: {str(e)}")
    
    def search_similar_pdfs(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar PDFs based on content"""
        try:
            # Generate embeddings for query
            query_embeddings = self.model.encode([query], convert_to_numpy=True)[0].tolist()
            
            # Search in vector index
            search_body = {
                'query': {
                    'knn': {
                        'vector': {
                            'vector': query_embeddings,
                            'k': top_k
                        }
                    }
                },
                '_source': ['pdf_id', 'filename', 'text', 'title', 'author']
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'pdf_id': hit['_source']['pdf_id'],
                    'filename': hit['_source']['filename'],
                    'text': hit['_source']['text'],
                    'title': hit['_source']['title'],
                    'score': hit['_score']
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"Error searching similar PDFs: {str(e)}") 
    
    def search_similar_content(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search for similar content and return text with sources for RAG"""
        try:
            # Generate embeddings for query
            query_embeddings = self.model.encode([query], convert_to_numpy=True)[0].tolist()
            
            # Search in vector index
            search_body = {
                'query': {
                    'knn': {
                        'vector': {
                            'vector': query_embeddings,
                            'k': max_results
                        }
                    }
                },
                '_source': ['pdf_id', 'filename', 'text', 'title', 'author']
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'content': hit['_source']['text'],
                    'filename': hit['_source']['filename'],
                    'pdf_id': hit['_source']['pdf_id'],
                    'score': hit['_score']
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching similar content: {str(e)}")
            return [] 