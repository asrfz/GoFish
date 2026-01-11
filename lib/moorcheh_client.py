"""
Moorcheh client for GoFish
Handles namespace creation, document upload, and search operations
"""
import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

MOORCHEH_API_KEY = os.getenv("MOORCHEH_API_KEY")
MOORCHEH_BASE_URL = os.getenv("MOORCHEH_BASE_URL", "https://api.moorcheh.ai")


class GoFishMoorchehClient:
    """Client for interacting with Moorcheh API"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or MOORCHEH_API_KEY
        self.base_url = base_url or MOORCHEH_BASE_URL
        
        if not self.api_key:
            raise ValueError("MOORCHEH_API_KEY not found in environment variables")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_namespace(self, namespace: str, namespace_type: str = "text") -> bool:
        """Create a Moorcheh namespace"""
        try:
            url = f"{self.base_url}/v1/namespaces"
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"namespace": namespace, "type": namespace_type},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                print(f"[OK] Created namespace: {namespace}")
                return True
            elif response.status_code == 409 or "already exists" in response.text.lower():
                print(f"[INFO] Namespace {namespace} already exists (continuing...)")
                return True
            else:
                print(f"[WARN] Namespace creation returned {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"[WARN] Namespace creation error: {e} (continuing...)")
            return False
    
    def upload_documents(self, namespace: str, documents: List[Dict[str, Any]], batch_size: int = 50) -> bool:
        """Upload documents to a Moorcheh namespace"""
        try:
            url = f"{self.base_url}/v1/namespaces/{namespace}/documents"
            
            # Upload in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json={"documents": batch},
                    timeout=60
                )
                
                if response.status_code in [200, 201]:
                    print(f"[OK] Uploaded batch {i//batch_size + 1} ({len(batch)} documents)")
                else:
                    print(f"[WARN] Upload batch {i//batch_size + 1} returned {response.status_code}: {response.text[:200]}")
            
            return True
        except Exception as e:
            print(f"[ERROR] Upload error: {e}")
            return False
    
    def search(self, namespace: str, query: str, top_k: int = 5, metadata_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search a Moorcheh namespace"""
        try:
            # Try /v1/search endpoint first
            url = f"{self.base_url}/v1/search"
            payload = {
                "namespace": namespace,
                "query": query,
                "top_k": top_k
            }
            
            if metadata_filters:
                payload["metadata_filters"] = metadata_filters
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Normalize response format
                if "snippets" in data:
                    return data
                elif "results" in data:
                    return {"snippets": data["results"]}
                elif isinstance(data, list):
                    return {"snippets": data}
                else:
                    return {"snippets": []}
            
            # Try /v1/retrieve as fallback
            url = f"{self.base_url}/v1/retrieve"
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return {"snippets": data}
                elif "results" in data:
                    return {"snippets": data["results"]}
                else:
                    return {"snippets": []}
            
            print(f"[WARN] Search returned {response.status_code}: {response.text[:200]}")
            return {"snippets": []}
            
        except Exception as e:
            print(f"[ERROR] Search error: {e}")
            return {"snippets": []}

