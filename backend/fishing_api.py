from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
import math
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

app = FastAPI(
    title="Ontario Angler Pro API",
    description="Real fishing spots from Ontario habitat data",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"

# Species keyword mapping for habitat matching
SPECIES_KEYWORDS = {
    "walleye": ["walleye", "pickerel", "yellow pickerel"],
    "bass": ["bass", "smallmouth", "largemouth", "smallmouth bass", "largemouth bass"],
    "trout": ["trout", "brook trout", "rainbow trout", "lake trout"],
    "pike": ["pike", "northern pike", "muskellunge", "muskie", "gar pike"],
    "perch": ["perch", "yellow perch"],
}

# Load GeoJSON on startup
GEOJSON_PATH = Path(__file__).parent / "fish_hab_type_wgs84_scored.geojson"
fishing_spots = []
SCORE_MIN = 1.0
SCORE_MAX = 1.0

def load_fishing_spots():
    global fishing_spots, SCORE_MIN, SCORE_MAX
    with open(GEOJSON_PATH, "r") as f:
        data = json.load(f)
        fishing_spots = data.get("features", [])
    
    # Calculate score range for normalization
    scores = [
        f["properties"].get("potential_score", 0) 
        for f in fishing_spots 
        if f["properties"].get("potential_score") is not None and f["properties"].get("potential_score") > 0
    ]
    if scores:
        SCORE_MIN = min(scores)
        SCORE_MAX = max(scores)
    
    print(f"Loaded {len(fishing_spots)} fishing spots from GeoJSON")
    print(f"Score range: {SCORE_MIN:.2f} to {SCORE_MAX:.2f}")

load_fishing_spots()


def normalize_score(raw_score: float) -> float:
    """Normalize score to 0-100 using log scale to handle huge variance."""
    if raw_score <= 0:
        return 0
    log_score = math.log(raw_score)
    log_min = math.log(SCORE_MIN)
    log_max = math.log(SCORE_MAX)
    if log_max == log_min:
        return 50
    return 100 * (log_score - log_min) / (log_max - log_min)


def species_matches_habitat(species: str, habitat_fe: str) -> tuple[float, str]:
    """
    Returns (match_multiplier, reason) based on species-habitat keyword match.
    - 1.5 = species explicitly mentioned (e.g., "walleye spawning")
    - 1.0 = generic favorable habitat (spawning/nursery)
    - 0.5 = unknown/generic habitat
    """
    if not habitat_fe:
        return 0.5, "Unknown habitat"
    
    habitat_lower = habitat_fe.lower()
    keywords = SPECIES_KEYWORDS.get(species, [])
    
    for kw in keywords:
        if kw in habitat_lower:
            return 1.5, f"Known {species} habitat"
    
    # Check for generic favorable habitats
    if any(term in habitat_lower for term in ["spawning", "nursery", "feeding", "rearing"]):
        return 1.0, "Favorable habitat type"
    
    return 0.5, "Generic habitat"


async def fetch_weather(lat: float, lon: float) -> dict:
    """Get weather for a location."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                OPEN_METEO_API,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,pressure_msl,wind_speed_10m",
                    "timezone": "America/Toronto"
                }
            )
            if response.status_code == 200:
                current = response.json().get("current", {})
                return {
                    "temperature": current.get("temperature_2m", 10),
                    "pressure": current.get("pressure_msl", 1013),
                    "wind_speed": current.get("wind_speed_10m", 10),
                }
    except Exception as e:
        print(f"Weather error: {e}")
    return {"temperature": 10, "pressure": 1013, "wind_speed": 10}


async def fetch_weather_for_regions(spots: list) -> dict:
    """Fetch weather for unique region clusters (rounded to 0.5 degree grid)."""
    clusters = {}
    for spot in spots:
        # Round to nearest 0.5 degree for clustering
        lat_key = round(spot["latitude"] * 2) / 2
        lon_key = round(spot["longitude"] * 2) / 2
        key = (lat_key, lon_key)
        if key not in clusters:
            clusters[key] = None
    
    # Fetch weather for up to 8 unique regions
    region_keys = list(clusters.keys())[:8]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for lat, lon in region_keys:
            try:
                response = await client.get(
                    OPEN_METEO_API,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "temperature_2m,pressure_msl,wind_speed_10m",
                        "timezone": "America/Toronto"
                    }
                )
                if response.status_code == 200:
                    current = response.json().get("current", {})
                    clusters[(lat, lon)] = {
                        "temperature": current.get("temperature_2m", 10),
                        "pressure": current.get("pressure_msl", 1013),
                        "wind_speed": current.get("wind_speed_10m", 10),
                    }
            except Exception as e:
                print(f"Weather error for ({lat}, {lon}): {e}")
    
    # Fill in default weather for unfetched regions
    default_weather = {"temperature": 10, "pressure": 1013, "wind_speed": 10}
    for key in clusters:
        if clusters[key] is None:
            clusters[key] = default_weather
    
    return clusters


def get_spot_weather(spot: dict, weather_cache: dict) -> dict:
    """Get weather for a spot from the region cache."""
    lat_key = round(spot["latitude"] * 2) / 2
    lon_key = round(spot["longitude"] * 2) / 2
    return weather_cache.get((lat_key, lon_key), {"temperature": 10, "pressure": 1013, "wind_speed": 10})


def calculate_score(species: str, base_score: float, habitat_multiplier: float, weather: dict, hour: int) -> dict:
    """
    Calculate bite score using weighted components:
    - 50% Habitat quality (base_score adjusted by species match)
    - 30% Weather conditions  
    - 20% Time of day
    This prevents all scores from capping at 100.
    """
    reasons = []
    
    is_low_light = hour < 7 or hour > 19
    temp = weather["temperature"]
    pressure = weather["pressure"]
    wind = weather["wind_speed"]
    
    # Component 1: Habitat score (0-100, scaled by species match)
    # habitat_multiplier: 1.5 = species match, 1.0 = favorable, 0.5 = unknown
    if habitat_multiplier >= 1.5:
        habitat_score = base_score  # Keep full score for matching species
        reasons.append(f"Prime {species} habitat")
    elif habitat_multiplier >= 1.0:
        habitat_score = base_score * 0.7  # 70% for favorable but not species-specific
        reasons.append("Favorable habitat")
    else:
        habitat_score = base_score * 0.4  # 40% for unknown habitat
        reasons.append("Unknown habitat")
    
    # Component 2: Weather score (0-100)
    weather_score = 50  # Baseline
    
    if species == "walleye":
        if pressure < 1010:
            weather_score += 20
            reasons.append("Falling pressure")
        elif pressure < 1015:
            weather_score += 10
        if 10 <= temp <= 18:
            weather_score += 20
            reasons.append("Optimal temp")
        elif temp < 5 or temp > 22:
            weather_score -= 20
            reasons.append("Poor temp")
    elif species == "trout":
        if 8 <= temp <= 16:
            weather_score += 30
            reasons.append("Ideal cool water")
        elif temp > 20:
            weather_score -= 30
            reasons.append("Too warm")
        if wind < 10:
            weather_score += 10
    elif species == "bass":
        if temp > 20:
            weather_score += 30
            reasons.append("Prime warm water")
        elif temp > 15:
            weather_score += 15
        elif temp < 12:
            weather_score -= 20
            reasons.append("Too cold")
    elif species == "pike":
        if 15 <= temp <= 22:
            weather_score += 25
            reasons.append("Optimal pike temp")
        if pressure < 1012:
            weather_score += 10
    elif species == "perch":
        if 12 <= temp <= 20:
            weather_score += 20
            reasons.append("Good perch temp")
        if pressure > 1015:
            weather_score += 15
            reasons.append("Stable pressure")
    
    weather_score = max(0, min(100, weather_score))
    
    # Component 3: Time of day score (0-100)
    time_score = 50  # Baseline
    
    if species in ["walleye", "pike"]:
        # Low light predators
        if is_low_light:
            time_score = 90
            reasons.append("Prime feeding time")
        elif 7 <= hour <= 9 or 17 <= hour <= 19:
            time_score = 75
        else:
            time_score = 40
    elif species == "bass":
        if is_low_light:
            time_score = 80
            reasons.append("Dawn/dusk activity")
        elif 10 <= hour <= 14:
            time_score = 50
        else:
            time_score = 60
    elif species == "trout":
        # Cooler parts of day
        if 6 <= hour <= 10:
            time_score = 85
            reasons.append("Morning feed")
        elif 16 <= hour <= 20:
            time_score = 80
        elif 11 <= hour <= 15:
            time_score = 40
        else:
            time_score = 60
    else:
        time_score = 60  # Perch and others
    
    # Weighted final score: 50% habitat, 30% weather, 20% time
    final_score = (habitat_score * 0.50) + (weather_score * 0.30) + (time_score * 0.20)
    final_score = max(0, min(100, final_score))
    
    if final_score >= 75:
        status = "Great"
    elif final_score >= 55:
        status = "Good"
    elif final_score >= 35:
        status = "Fair"
    else:
        status = "Poor"
    
    return {
        "score": int(final_score),
        "status": status,
        "reasoning": "; ".join(reasons) if reasons else "Standard conditions"
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "spots_loaded": len(fishing_spots), "version": "3.0.0"}


@app.get("/api/fishing-spots")
async def get_fishing_spots(
    species: str = "walleye",
    limit: int = Query(default=100, le=500),
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
):
    """Get top fishing spots sorted by species-specific bite score."""
    current_hour = datetime.now().hour
    
    # Filter spots and calculate species match
    filtered = []
    for spot in fishing_spots:
        props = spot.get("properties", {})
        lat = props.get("centroid_lat_wgs84")
        lon = props.get("centroid_lon_wgs84")
        potential = props.get("potential_score_capped") or props.get("potential_score") or 0
        habitat_fe = props.get("HABITAT_FE", "")
        
        if lat is None or lon is None:
            continue
            
        # Apply bounding box filter if provided
        if min_lat and lat < min_lat:
            continue
        if max_lat and lat > max_lat:
            continue
        if min_lon and lon < min_lon:
            continue
        if max_lon and lon > max_lon:
            continue
        
        # Calculate species-habitat match
        habitat_mult, habitat_reason = species_matches_habitat(species, habitat_fe)
        
        # Normalize base score (log scale)
        base_score = normalize_score(potential)
        
        filtered.append({
            "id": props.get("UNIQID", ""),
            "name": props.get("LAKE_NAME", "Unknown"),
            "latitude": lat,
            "longitude": lon,
            "potential_score": potential,
            "base_score": round(base_score, 1),
            "habitat_type": habitat_fe,
            "habitat_desc": props.get("HABITAT_DE", ""),
            "habitat_match": habitat_mult,
            "habitat_reason": habitat_reason,
            "area": props.get("AREA", 0),
        })
    
    # Sort by habitat match first (species-specific spots), then by base score
    filtered.sort(key=lambda x: (x["habitat_match"], x["base_score"]), reverse=True)
    top_spots = filtered[:limit]
    
    # Fetch weather for all regions
    weather_cache = await fetch_weather_for_regions(top_spots)
    
    # Calculate final bite scores with weather
    results = []
    for spot in top_spots:
        weather = get_spot_weather(spot, weather_cache)
        bite = calculate_score(
            species, 
            spot["base_score"], 
            spot["habitat_match"], 
            weather, 
            current_hour
        )
        results.append({
            **spot,
            "weather": weather,
            "bite_score": bite["score"],
            "status": bite["status"],
            "reasoning": f"{spot['habitat_reason']}; {bite['reasoning']}"
        })
    
    # Final sort by bite score
    results.sort(key=lambda x: x["bite_score"], reverse=True)
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "species": species,
        "total_spots": len(fishing_spots),
        "returned": len(results),
        "spots": results,
    }


@app.get("/api/best-spot")
async def get_best_spot(species: str = "walleye"):
    """Get the single best fishing spot for a species."""
    data = await get_fishing_spots(species=species, limit=1)
    if data["spots"]:
        return {"best": data["spots"][0], "timestamp": data["timestamp"]}
    return {"best": None, "timestamp": data["timestamp"]}


@app.get("/api/species")
async def get_supported_species():
    """Get list of supported species for filtering."""
    return {
        "species": list(SPECIES_KEYWORDS.keys()),
        "descriptions": {
            "walleye": "Best in low light, falling pressure",
            "bass": "Active in warm water, dawn/dusk",
            "trout": "Prefer cool water (8-16°C)",
            "pike": "Ambush predators, active in moderate temps",
            "perch": "Stable pressure, moderate temps",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
