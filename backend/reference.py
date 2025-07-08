from langchain_core.documents.base import Blob

blob = Blob.from_path("./attn.pdf")

from langchain_community.document_loaders.parsers import PyMuPDFParser

parser = PyMuPDFParser(
    # password = None,
    mode = "single",
    pages_delimiter = "")


docs = []
docs_lazy = parser.lazy_parse(blob)

for doc in docs_lazy:
    docs.append(doc)



texts = []

for doc in docs:
    for lines in doc.page_content.split('.'):
        texts.append(lines)
from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch
import json

model = SentenceTransformer('all-MiniLM-L6-v2')  


vectors = model.encode(texts, convert_to_numpy=True)


client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 63350}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False
)

index_name = 'test'
if client.indices.exists(index=index_name):
    client.indices.delete(index=index_name)

index_body = {
    "settings": {
        "index": {
            "knn": True
        }
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text"
            },
            "content": {
                "type": "text"
            },
            "author": {
                "type": "keyword"
            },
            "vector": {
                "type": "knn_vector",
                "dimension": 384,  # all-MiniLM-L6-v2
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

response = client.indices.create(index=index_name, body=index_body)

for i, (text, vector) in enumerate(zip(texts, vectors)):
    doc = {
        "text": text,
        "vector": vector.tolist(),
        "title": f"title_{i}",
        "arthor": f"arthor_{i}",
    }
    response = client.index(index=index_name, id=i, body=doc)