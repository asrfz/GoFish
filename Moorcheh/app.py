"""
GoFish Brain API - Moorcheh-powered fishing assistant
Evidence-based safety and recipe guidance using Moorcheh Memory-in-a-Box
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from lib.moorcheh_client import GoFishMoorchehClient
from brain_agent import (
    determine_edibility_label,
    extract_safety_summary,
    extract_recipe_cards,
    extract_community_alerts,
    filter_community_by_recency
)

load_dotenv()

app = FastAPI(
    title="GoFish Brain API",
    description="Moorcheh-powered fishing assistant - Evidence-based safety & recipe guidance",
    version="1.0.0"
)

# Initialize Moorcheh client
moorcheh_client = GoFishMoorchehClient()

# Namespaces
NS_SAFETY = os.getenv("NS_SAFETY", "safety_memory")
NS_RECIPES = os.getenv("NS_RECIPES", "recipe_memory")
NS_COMMUNITY = os.getenv("NS_COMMUNITY", "community_memory")


# Pydantic models
class Preferences(BaseModel):
    avoid_high_mercury: bool = False
    pregnant: bool = False
    catch_and_release: bool = False


class IdentifyRequest(BaseModel):
    species: str
    spot: Optional[str] = None
    preferences: Preferences = Preferences()


class SnippetResponse(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]
    namespace: Optional[str] = None


class RecipeCard(BaseModel):
    title: str
    steps: List[str]
    source_snippet: str


class IdentifyResponse(BaseModel):
    species: str
    spot: Optional[str]
    edibility_label: str
    safety_summary: List[str]
    recipes: List[RecipeCard]
    community_alerts: List[str]
    evidence: Dict[str, List[SnippetResponse]]


def build_safety_query(species: str, spot: Optional[str], preferences: Preferences) -> str:
    """Build safety query string"""
    query = f"Safety and edibility guidance for {species} in Ontario"
    if spot:
        query += f" at {spot}"
    
    prefs = []
    if preferences.avoid_high_mercury:
        prefs.append("avoid high mercury")
    if preferences.pregnant:
        prefs.append("pregnant")
    
    if prefs:
        query += f". User preferences: {', '.join(prefs)}"
    
    return query


def build_recipe_query(species: str, preferences: Preferences) -> str:
    """Build recipe query string"""
    query = f"Quick recipe ideas for {species}"
    
    prefs = []
    if preferences.avoid_high_mercury:
        prefs.append("low mercury")
    if preferences.pregnant:
        prefs.append("safe for pregnancy")
    
    if prefs:
        query += f" that match preferences: {', '.join(prefs)}"
    
    return query


def build_community_query(spot: str) -> str:
    """Build community query string"""
    return f"Recent safety and conditions reports for {spot}"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gofish-brain-api"}


@app.post("/brain/advise", response_model=IdentifyResponse)
async def brain_advise(request: IdentifyRequest):
    """
    Main brain endpoint: Multi-namespace retrieval + evidence-based decision making
    """
    try:
        # 1. Safety search
        safety_query = build_safety_query(request.species, request.spot, request.preferences)
        safety_metadata = {
            "species": request.species,
            "region": "ontario",
            "type": "safety"
        }
        if request.spot:
            safety_metadata["spot"] = request.spot
        
        safety_results = moorcheh_client.search(
            namespace=NS_SAFETY,
            query=safety_query,
            top_k=5,
            metadata_filters=safety_metadata
        )
        safety_snippets = safety_results.get("snippets", [])
        
        # 2. Recipe search
        recipe_query = build_recipe_query(request.species, request.preferences)
        recipe_metadata = {
            "species": request.species,
            "region": "ontario",
            "type": "recipe"
        }
        recipe_results = moorcheh_client.search(
            namespace=NS_RECIPES,
            query=recipe_query,
            top_k=5,
            metadata_filters=recipe_metadata
        )
        recipe_snippets = recipe_results.get("snippets", [])
        
        # 3. Community search
        community_snippets = []
        if request.spot:
            community_query = build_community_query(request.spot)
            community_metadata = {
                "spot": request.spot,
                "region": "ontario",
                "type": "community"
            }
            community_results = moorcheh_client.search(
                namespace=NS_COMMUNITY,
                query=community_query,
                top_k=5,
                metadata_filters=community_metadata
            )
            community_snippets = community_results.get("snippets", [])
            community_snippets = filter_community_by_recency(community_snippets)
        
        # 4. Agent logic
        edibility_label = determine_edibility_label(
            safety_snippets,
            community_snippets,
            request.preferences.dict()
        )
        
        safety_summary = extract_safety_summary(safety_snippets, max_bullets=3)
        recipe_cards = extract_recipe_cards(recipe_snippets, max_recipes=2)
        community_alerts = extract_community_alerts(community_snippets, max_alerts=3)
        
        # 5. Format evidence
        evidence = {
            "safety": [
                SnippetResponse(
                    text=s.get("text", ""),
                    score=s.get("score", 0.0),
                    metadata=s.get("metadata", {}),
                    namespace=NS_SAFETY
                )
                for s in safety_snippets
            ],
            "recipes": [
                SnippetResponse(
                    text=s.get("text", ""),
                    score=s.get("score", 0.0),
                    metadata=s.get("metadata", {}),
                    namespace=NS_RECIPES
                )
                for s in recipe_snippets
            ],
            "community": [
                SnippetResponse(
                    text=s.get("text", ""),
                    score=s.get("score", 0.0),
                    metadata=s.get("metadata", {}),
                    namespace=NS_COMMUNITY
                )
                for s in community_snippets
            ]
        }
        
        return IdentifyResponse(
            species=request.species,
            spot=request.spot,
            edibility_label=edibility_label,
            safety_summary=safety_summary,
            recipes=recipe_cards,
            community_alerts=community_alerts,
            evidence=evidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in brain analysis: {str(e)}")


class IngestCommunityRequest(BaseModel):
    spot: str
    handle: str
    text: str
    timestamp: Optional[str] = None


@app.post("/memory/ingestCommunity")
async def ingest_community(request: IngestCommunityRequest):
    """
    Ingest a new community report into Moorcheh memory (real-time update)
    """
    try:
        timestamp = request.timestamp or datetime.now().isoformat()
        
        document = {
            "id": f"community-{int(datetime.now().timestamp())}",
            "text": request.text,
            "metadata": {
                "spot": request.spot,
                "region": "ontario",
                "type": "community",
                "risk_level": "edible",
                "risk_tags": [],
                "timestamp": timestamp,
                "handle": request.handle,
                "source": "USER"
            }
        }
        
        moorcheh_client.upload_documents(NS_COMMUNITY, [document], batch_size=1)
        
        return {
            "status": "success",
            "message": "Community report ingested into Moorcheh memory",
            "document_id": document["id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting community report: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve frontend"""
    html_path = Path(__file__).parent / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content="<h1>GoFish Brain API</h1><p>Use /brain/advise endpoint</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

