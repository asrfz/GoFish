"""
Generate synthetic fishing spots for Ontario areas not covered by the original GeoJSON.
This adds spots for Lake Ontario, Lake Erie, Ottawa River, Lake Simcoe, and Kawartha Lakes.
"""

import json
import random
from pathlib import Path

# Ontario fishing locations to generate
ONTARIO_FISHING_AREAS = [
    # Lake Ontario shoreline (lat ~43.2-44.2)
    {"name": "Toronto Islands", "lat": 43.62, "lon": -79.38, "type": "urban"},
    {"name": "Scarborough Bluffs", "lat": 43.71, "lon": -79.23, "type": "shore"},
    {"name": "Ajax Waterfront", "lat": 43.85, "lon": -79.03, "type": "shore"},
    {"name": "Whitby Harbour", "lat": 43.87, "lon": -78.94, "type": "harbour"},
    {"name": "Oshawa Harbour", "lat": 43.86, "lon": -78.83, "type": "harbour"},
    {"name": "Port Hope", "lat": 43.95, "lon": -78.29, "type": "harbour"},
    {"name": "Cobourg Beach", "lat": 43.96, "lon": -78.17, "type": "shore"},
    {"name": "Brighton Bay", "lat": 44.05, "lon": -77.75, "type": "bay"},
    {"name": "Belleville Bay", "lat": 44.16, "lon": -77.38, "type": "bay"},
    {"name": "Kingston Harbour", "lat": 44.23, "lon": -76.48, "type": "harbour"},
    {"name": "Wolfe Island", "lat": 44.18, "lon": -76.35, "type": "island"},
    {"name": "Amherst Island", "lat": 44.15, "lon": -76.70, "type": "island"},
    {"name": "Prince Edward County", "lat": 43.95, "lon": -77.15, "type": "shore"},
    {"name": "Presqu'ile Bay", "lat": 43.99, "lon": -77.72, "type": "bay"},
    {"name": "Hamilton Harbour", "lat": 43.28, "lon": -79.79, "type": "harbour"},
    {"name": "Burlington Bay", "lat": 43.32, "lon": -79.80, "type": "bay"},
    {"name": "Niagara-on-the-Lake", "lat": 43.26, "lon": -79.07, "type": "shore"},
    {"name": "St. Catharines", "lat": 43.18, "lon": -79.24, "type": "shore"},
    
    # Lake Erie (lat ~41.8-42.8)
    {"name": "Port Dover", "lat": 42.79, "lon": -80.20, "type": "harbour"},
    {"name": "Long Point Bay", "lat": 42.58, "lon": -80.05, "type": "bay"},
    {"name": "Port Stanley", "lat": 42.67, "lon": -81.22, "type": "harbour"},
    {"name": "Rondeau Bay", "lat": 42.30, "lon": -81.85, "type": "bay"},
    {"name": "Point Pelee", "lat": 41.96, "lon": -82.52, "type": "shore"},
    {"name": "Leamington", "lat": 42.05, "lon": -82.60, "type": "shore"},
    {"name": "Kingsville", "lat": 42.03, "lon": -82.74, "type": "shore"},
    
    # Ottawa River area
    {"name": "Ottawa River - Britannia", "lat": 45.36, "lon": -75.80, "type": "river"},
    {"name": "Ottawa River - Petrie Island", "lat": 45.49, "lon": -75.50, "type": "island"},
    {"name": "Rideau River", "lat": 45.38, "lon": -75.68, "type": "river"},
    {"name": "Gatineau River", "lat": 45.48, "lon": -75.72, "type": "river"},
    {"name": "Lac Deschenes", "lat": 45.40, "lon": -75.93, "type": "lake"},
    {"name": "Calabogie Lake", "lat": 45.30, "lon": -76.75, "type": "lake"},
    {"name": "Mississippi River", "lat": 45.23, "lon": -76.35, "type": "river"},
    
    # Lake Simcoe area
    {"name": "Lake Simcoe - Barrie", "lat": 44.38, "lon": -79.68, "type": "lake"},
    {"name": "Lake Simcoe - Orillia", "lat": 44.60, "lon": -79.42, "type": "lake"},
    {"name": "Kempenfelt Bay", "lat": 44.38, "lon": -79.65, "type": "bay"},
    {"name": "Cook's Bay", "lat": 44.25, "lon": -79.50, "type": "bay"},
    {"name": "Georgina Island", "lat": 44.35, "lon": -79.40, "type": "island"},
    {"name": "Beaverton", "lat": 44.43, "lon": -79.15, "type": "shore"},
    {"name": "Lake Couchiching", "lat": 44.65, "lon": -79.38, "type": "lake"},
    
    # Kawartha Lakes
    {"name": "Pigeon Lake", "lat": 44.45, "lon": -78.48, "type": "lake"},
    {"name": "Sturgeon Lake", "lat": 44.52, "lon": -78.73, "type": "lake"},
    {"name": "Balsam Lake", "lat": 44.58, "lon": -78.83, "type": "lake"},
    {"name": "Cameron Lake", "lat": 44.55, "lon": -78.78, "type": "lake"},
    {"name": "Buckhorn Lake", "lat": 44.53, "lon": -78.35, "type": "lake"},
    {"name": "Chemong Lake", "lat": 44.45, "lon": -78.33, "type": "lake"},
    {"name": "Rice Lake", "lat": 44.15, "lon": -78.10, "type": "lake"},
    {"name": "Stony Lake", "lat": 44.55, "lon": -78.05, "type": "lake"},
    
    # Peterborough Area
    {"name": "Little Lake", "lat": 44.30, "lon": -78.32, "type": "lake"},
    {"name": "Otonabee River - Downtown", "lat": 44.31, "lon": -78.32, "type": "river"},
    {"name": "Otonabee River - Trent U", "lat": 44.36, "lon": -78.29, "type": "river"},
    {"name": "Rice Lake - Bewdley", "lat": 44.09, "lon": -78.28, "type": "lake"},
    {"name": "Chemung Lake - Bridgenorth", "lat": 44.39, "lon": -78.38, "type": "lake"},
    
    # Muskoka Lakes (supplement existing data)
    {"name": "Lake Muskoka", "lat": 44.98, "lon": -79.45, "type": "lake"},
    {"name": "Lake Rosseau", "lat": 45.08, "lon": -79.58, "type": "lake"},
    {"name": "Lake Joseph", "lat": 45.05, "lon": -79.70, "type": "lake"},
    {"name": "Lake of Bays", "lat": 45.25, "lon": -79.02, "type": "lake"},
    
    # Northern Ontario (supplement)
    {"name": "Lake Nipissing", "lat": 46.30, "lon": -79.50, "type": "lake"},
    {"name": "Lake Temiskaming", "lat": 47.50, "lon": -79.70, "type": "lake"},
    {"name": "Lake Temagami", "lat": 47.05, "lon": -80.05, "type": "lake"},
]

# Species that match each habitat type
HABITAT_SPECIES = {
    "urban": ["bass", "perch", "carp"],
    "shore": ["walleye", "bass", "perch", "pike"],
    "harbour": ["walleye", "perch", "bass"],
    "bay": ["walleye", "bass", "pike", "perch"],
    "island": ["walleye", "bass", "trout", "pike"],
    "river": ["walleye", "bass", "trout", "pike"],
    "lake": ["walleye", "bass", "trout", "pike", "perch"],
}

HABITAT_DESCRIPTIONS = {
    "walleye": "Walleye spawning and feeding habitat",
    "bass": "Smallmouth and largemouth bass spawning/nursery area",
    "trout": "Cold water trout habitat with adequate depth",
    "pike": "Northern pike spawning and ambush habitat",
    "perch": "Yellow perch feeding and nursery area",
}

def generate_synthetic_spots():
    """Generate synthetic fishing spots with realistic properties."""
    spots = []
    
    for i, area in enumerate(ONTARIO_FISHING_AREAS):
        # Generate 3-8 spots per area
        num_spots = random.randint(3, 8)
        
        for j in range(num_spots):
            # Slightly vary the coordinates
            lat_offset = random.uniform(-0.05, 0.05)
            lon_offset = random.uniform(-0.05, 0.05)
            
            # Choose species based on habitat type
            possible_species = HABITAT_SPECIES.get(area["type"], ["bass", "perch"])
            primary_species = random.choice(possible_species)
            
            # Generate realistic scores
            area_size = random.uniform(1000, 50000)
            edge_density = random.uniform(0.02, 0.15)
            potential_score = area_size * edge_density * random.uniform(50, 200)
            
            spot = {
                "type": "Feature",
                "properties": {
                    "UNIQID": f"SYN-{area['name'][:3].upper()}-{i}-{j}",
                    "LAKE_NAME": area["name"],
                    "HABITAT_FE": HABITAT_DESCRIPTIONS.get(primary_species, "General fish habitat"),
                    "HABITAT_DE": f"{area['type'].capitalize()} habitat suitable for {', '.join(possible_species)}",
                    "AREA": area_size,
                    "PERIMETER": area_size * edge_density * 10,
                    "TYPE": 1.0,
                    "INFO_1": "Synthetic data for demonstration",
                    "centroid_lat_wgs84": area["lat"] + lat_offset,
                    "centroid_lon_wgs84": area["lon"] + lon_offset,
                    "edge_density": edge_density,
                    "edge_norm": edge_density * 10,
                    "potential_score": potential_score,
                    "potential_score_capped": min(potential_score, 100000),
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [area["lon"] + lon_offset, area["lat"] + lat_offset]
                }
            }
            spots.append(spot)
    
    return spots


def merge_with_existing(existing_path: Path, output_path: Path):
    """Merge synthetic spots with existing GeoJSON data."""
    # Load existing data
    with open(existing_path, "r") as f:
        existing = json.load(f)
    
    print(f"Existing features: {len(existing['features'])}")
    
    # Generate and add synthetic spots
    synthetic = generate_synthetic_spots()
    print(f"Generated synthetic features: {len(synthetic)}")
    
    # Merge
    existing["features"].extend(synthetic)
    print(f"Total features: {len(existing['features'])}")
    
    # Save merged file
    with open(output_path, "w") as f:
        json.dump(existing, f)
    
    print(f"Saved to: {output_path}")
    
    # Print geographic coverage
    lats = [f["properties"].get("centroid_lat_wgs84") for f in existing["features"] if f["properties"].get("centroid_lat_wgs84")]
    lons = [f["properties"].get("centroid_lon_wgs84") for f in existing["features"] if f["properties"].get("centroid_lon_wgs84")]
    print(f"New lat range: {min(lats):.2f} to {max(lats):.2f}")
    print(f"New lon range: {min(lons):.2f} to {max(lons):.2f}")


if __name__ == "__main__":
    base_path = Path(__file__).parent
    existing = base_path / "fish_hab_type_wgs84_scored.geojson"
    output = base_path / "fish_hab_type_wgs84_scored.geojson"  # Overwrite
    
    merge_with_existing(existing, output)
