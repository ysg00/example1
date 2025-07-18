import os
import requests
from typing import List, Optional
from ..services.opensearch_service import OpenSearchService

class ChatService:
    def __init__(self):
        self.ollama_url = "http://studio.local:11434/api/generate"
        self.model_name = "llama3.3"
        self.opensearch_service = OpenSearchService()
        
        # Test Ollama connection on initialization
        self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test connection to Ollama endpoint"""
        try:
            response = requests.get("http://studio.local:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama connection successful")
                return True
            else:
                print(f"⚠️ Ollama connection failed with status: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️ Ollama connection failed: {e}")
            return False
    
    def _format_prompt(self, query: str, context: Optional[str] = None) -> str:
        """Format the prompt for Llama 3.3"""
        if context:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant. Use the following context to answer the user's question. If the context doesn't contain relevant information, say so.

Context:
{context}

<|eot_id|><|start_header_id|>user<|end_header_id|>

{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        else:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant. Answer the user's question to the best of your ability.

<|eot_id|><|start_header_id|>user<|end_header_id|>

{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return prompt
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response using Ollama API"""
        try:
            # Prepare the request payload for Ollama
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 512
                }
            }
            
            # Make request to Ollama
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                
                # Extract only the assistant's response if it contains the special tokens
                if "<|start_header_id|>assistant<|end_header_id|>" in generated_text:
                    generated_text = generated_text.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()
                
                return generated_text
            else:
                print(f"Ollama API error: {response.status_code} - {response.text}")
                return "I apologize, but there was an error communicating with the language model. Please try again."
                
        except requests.exceptions.Timeout:
            print("Ollama API request timed out")
            return "I apologize, but the request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            print("Failed to connect to Ollama API")
            return "I apologize, but I cannot connect to the language model service. Please check if the Ollama service is running."
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but there was an error generating the response. Please try again."
    
    def _search_knowledge_base(self, query: str) -> tuple[Optional[str], List[str]]:
        """Search the OpenSearch knowledge base for relevant context"""
        try:
            # Use the same embedding model as the OpenSearch service
            results = self.opensearch_service.search_similar_content(query, max_results=3)
            
            if not results:
                return None, []
            
            # Extract context and sources
            context_parts = []
            sources = []
            
            for result in results:
                content = result.get('content', '')
                filename = result.get('filename', 'Unknown')
                context_parts.append(content)
                sources.append(filename)
            
            context = "\n\n".join(context_parts)
            return context, sources
            
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return None, []
    
    def chat(self, query: str, use_knowledge: bool = True) -> tuple[str, List[str]]:
        """Main chat method that handles both RAG and direct LLM queries"""
        context = None
        sources = []
        
        if use_knowledge:
            # Search knowledge base for relevant context
            context, sources = self._search_knowledge_base(query)
        
        # Format prompt with or without context
        prompt = self._format_prompt(query, context)
        
        # Generate response
        response = self._generate_response(prompt)
        
        return response, sources 