"""
Evidence-based agent logic for GoFish Moorcheh Brain
Processes retrieved snippets to determine edibility labels and extract summaries
NO LLM - only processes retrieved evidence
"""
from typing import List, Dict, Any, Optional


def determine_edibility_label(
    safety_snippets: List[Dict[str, Any]],
    community_snippets: List[Dict[str, Any]],
    preferences: Dict[str, bool]
) -> str:
    """
    Determine edibility label based on retrieved evidence
    Returns: "EDIBLE", "CAUTION", "NOT_RECOMMENDED", or "UNKNOWN"
    """
    if not safety_snippets:
        return "UNKNOWN"
    
    # Check for NOT_RECOMMENDED
    for snippet in safety_snippets:
        metadata = snippet.get("metadata", {})
        risk_level = metadata.get("risk_level", "").lower()
        risk_tags = metadata.get("risk_tags", [])
        
        if risk_level == "not_recommended":
            return "NOT_RECOMMENDED"
        
        if preferences.get("pregnant", False):
            if "pregnancy_caution" in risk_tags or "pregnant" in str(risk_tags).lower():
                return "NOT_RECOMMENDED"
    
    # Check for CAUTION
    for snippet in safety_snippets:
        metadata = snippet.get("metadata", {})
        risk_level = metadata.get("risk_level", "").lower()
        risk_tags = metadata.get("risk_tags", [])
        
        if risk_level == "caution":
            return "CAUTION"
        
        if preferences.get("avoid_high_mercury", False):
            if "high_mercury" in risk_tags or "mercury" in str(risk_tags).lower():
                return "CAUTION"
    
    # Check community reports for caution
    for snippet in community_snippets:
        text = snippet.get("text", "").lower()
        if any(word in text for word in ["unsafe", "caution", "warning", "avoid", "bloom", "contaminated"]):
            return "CAUTION"
    
    # Default to EDIBLE if we have safety snippets
    return "EDIBLE"


def extract_safety_summary(safety_snippets: List[Dict[str, Any]], max_bullets: int = 3) -> List[str]:
    """Extract safety summary bullets from retrieved snippets"""
    bullets = []
    
    for snippet in safety_snippets[:max_bullets]:
        text = snippet.get("text", "").strip()
        if text:
            # Simple extraction: take first sentence or first 150 chars
            if "." in text:
                first_sentence = text.split(".")[0] + "."
            else:
                first_sentence = text[:150] + ("..." if len(text) > 150 else "")
            bullets.append(first_sentence)
    
    return bullets[:max_bullets]


def extract_recipe_cards(recipe_snippets: List[Dict[str, Any]], max_recipes: int = 2) -> List[Dict[str, Any]]:
    """Extract recipe cards from retrieved snippets"""
    recipes = []
    
    for snippet in recipe_snippets[:max_recipes]:
        text = snippet.get("text", "").strip()
        if not text:
            continue
        
        # Extract title (first part before colon or first sentence)
        if ":" in text:
            title = text.split(":")[0].strip()
            rest = ":".join(text.split(":")[1:]).strip()
        else:
            title = text.split(".")[0].strip() if "." in text else text[:50]
            rest = text
        
        # Extract steps (look for instruction-like patterns)
        steps = []
        lines = rest.split(". ")
        for line in lines[:5]:  # Max 5 steps
            line = line.strip()
            if line and len(line) > 10:  # Skip very short lines
                steps.append(line)
        
        recipes.append({
            "title": title,
            "steps": steps[:5] if steps else [rest[:200]],
            "source_snippet": text[:300]
        })
    
    return recipes[:max_recipes]


def extract_community_alerts(community_snippets: List[Dict[str, Any]], max_alerts: int = 3) -> List[str]:
    """Extract community alerts from retrieved snippets"""
    alerts = []
    
    for snippet in community_snippets[:max_alerts]:
        text = snippet.get("text", "").strip()
        if text:
            # Take first 200 chars
            alert = text[:200] + ("..." if len(text) > 200 else "")
            alerts.append(alert)
    
    return alerts[:max_alerts]


def filter_community_by_recency(community_snippets: List[Dict[str, Any]], days: int = 7) -> List[Dict[str, Any]]:
    """Filter community snippets by recency (if timestamp available)"""
    # For now, just return all snippets
    # In production, filter by timestamp in metadata
    return community_snippets

