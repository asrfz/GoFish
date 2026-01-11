"""
Ingest comprehensive seed dataset for GoFish Moorcheh Brain
6 species x (2 safety + 2 recipes + 1 handling) + 3 spots x 5 community reports
All chunks include proper metadata for filtering and personalization
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.moorcheh_client import GoFishMoorchehClient
from dotenv import load_dotenv

load_dotenv()

NS_SAFETY = os.getenv("NS_SAFETY", "safety_memory")
NS_RECIPES = os.getenv("NS_RECIPES", "recipe_memory")
NS_COMMUNITY = os.getenv("NS_COMMUNITY", "community_memory")

now = datetime.now()

# ============ SAFETY MEMORY ============
SAFETY_CHUNKS = [
    # Walleye
    {
        "id": "safety-walleye-1",
        "text": "Walleye from Ontario waters are generally safe to eat when following consumption guidelines. Check local advisories for specific water bodies. Limit consumption to 2-4 meals per month for adults. Low mercury levels make it suitable for pregnant women and children.",
        "metadata": {
            "species": "walleye",
            "spot": None,
            "region": "ontario",
            "type": "safety",
            "risk_level": "edible",
            "risk_tags": ["low_mercury"],
            "source": "DEMO"
        }
    },
    {
        "id": "safety-walleye-2",
        "text": "Walleye handling: Keep fish cold on ice immediately after catch. Clean and gut within 2 hours. Remove skin and fat to reduce potential contaminants. Cook thoroughly to 145°F internal temperature. Store on ice or refrigerate immediately.",
        "metadata": {
            "species": "walleye",
            "spot": None,
            "region": "ontario",
            "type": "handling",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Largemouth Bass
    {
        "id": "safety-bass-1",
        "text": "Largemouth bass from Ontario are safe to eat in moderation. Consumption advisory: 1-2 meals per month for general population. Pregnant women and children should limit to 1 meal per month due to moderate mercury levels.",
        "metadata": {
            "species": "largemouth_bass",
            "spot": None,
            "region": "ontario",
            "type": "safety",
            "risk_level": "caution",
            "risk_tags": ["moderate_mercury", "pregnancy_caution"],
            "source": "DEMO"
        }
    },
    {
        "id": "safety-bass-2",
        "text": "Bass cleaning tips: Use a sharp fillet knife. Remove all dark meat along the lateral line. Rinse fillets in cold water. Store on ice or refrigerate immediately. Best consumed within 2 days or freeze for later use.",
        "metadata": {
            "species": "largemouth_bass",
            "spot": None,
            "region": "ontario",
            "type": "handling",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Rainbow Trout
    {
        "id": "safety-trout-1",
        "text": "Rainbow trout from Ontario streams are excellent eating fish with low contaminant levels. Safe for regular consumption: 4-8 meals per month. High in omega-3 fatty acids. Safe for pregnant women and children. Low mercury levels.",
        "metadata": {
            "species": "rainbow_trout",
            "spot": None,
            "region": "ontario",
            "type": "safety",
            "risk_level": "edible",
            "risk_tags": ["low_mercury"],
            "source": "DEMO"
        }
    },
    {
        "id": "safety-trout-2",
        "text": "Trout preparation: Bleed fish immediately after catch by cutting gills. Keep in cold water or on ice. Remove scales if skin-on, or fillet skin-off. Trout is delicate - handle gently. Store on ice, best consumed fresh within 1-2 days.",
        "metadata": {
            "species": "rainbow_trout",
            "spot": None,
            "region": "ontario",
            "type": "handling",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Northern Pike
    {
        "id": "safety-pike-1",
        "text": "Northern pike from Ontario lakes may contain higher mercury levels. Consumption advisory: 1 meal per month for adults. Pregnant women, nursing mothers, and children under 15 should avoid consumption. Higher risk due to position in food chain.",
        "metadata": {
            "species": "northern_pike",
            "spot": None,
            "region": "ontario",
            "type": "safety",
            "risk_level": "not_recommended",
            "risk_tags": ["high_mercury", "pregnancy_caution"],
            "source": "DEMO"
        }
    },
    {
        "id": "safety-pike-2",
        "text": "Pike handling: Y-bones require special technique - remove by cutting along each side of the backbone. Pike can be aggressive - use proper grip when handling. Freeze unused portions immediately. Best consumed within 2 days.",
        "metadata": {
            "species": "northern_pike",
            "spot": None,
            "region": "ontario",
            "type": "handling",
            "risk_level": "caution",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Yellow Perch
    {
        "id": "safety-perch-1",
        "text": "Yellow perch are safe for regular consumption from most Ontario waters. Low mercury fish suitable for 4-8 meals per month. Good choice for families and pregnant women. Excellent source of lean protein with minimal contaminants.",
        "metadata": {
            "species": "yellow_perch",
            "spot": None,
            "region": "ontario",
            "type": "safety",
            "risk_level": "edible",
            "risk_tags": ["low_mercury"],
            "source": "DEMO"
        }
    },
    {
        "id": "safety-perch-2",
        "text": "Perch are small fish - usually eaten whole after scaling or as fillets. Scale fish thoroughly. Remove head and guts. Small bones are edible when cooked. Excellent pan-fried or deep-fried. Store on ice, consume within 2 days.",
        "metadata": {
            "species": "yellow_perch",
            "spot": None,
            "region": "ontario",
            "type": "handling",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Chinook Salmon
    {
        "id": "safety-salmon-1",
        "text": "Lake Ontario salmon (Chinook, Coho) are safe to eat following consumption guidelines. Limit to 2-4 meals per month. Higher in omega-3s but check for local PCB advisories near urban areas. Moderate mercury levels - avoid if pregnant.",
        "metadata": {
            "species": "chinook_salmon",
            "spot": None,
            "region": "ontario",
            "type": "safety",
            "risk_level": "caution",
            "risk_tags": ["moderate_mercury", "pregnancy_caution"],
            "source": "DEMO"
        }
    },
    {
        "id": "safety-salmon-2",
        "text": "Salmon handling: Keep on ice immediately after catch. Clean and gut promptly. Remove bloodline if present. Can be cooked fresh, smoked, or frozen. Freeze immediately if not consuming within 1-2 days. High fat content means it freezes well.",
        "metadata": {
            "species": "chinook_salmon",
            "spot": None,
            "region": "ontario",
            "type": "handling",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    }
]

# ============ RECIPE MEMORY ============
RECIPE_CHUNKS = [
    # Walleye Recipes
    {
        "id": "recipe-walleye-1",
        "text": "Classic Pan-Fried Walleye: Season fillets with salt, pepper, and paprika. Dredge in flour, dip in beaten egg, then coat with breadcrumbs. Pan-fry in butter over medium heat for 3-4 minutes per side until golden and flaky. Serve with lemon wedges.",
        "metadata": {
            "species": "walleye",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    {
        "id": "recipe-walleye-2",
        "text": "Walleye Fish Tacos: Cut walleye into strips, season with cumin and chili powder. Grill or pan-fry until cooked through. Serve in warm tortillas with cabbage slaw, avocado, and lime crema. Fresh and light meal perfect for summer.",
        "metadata": {
            "species": "walleye",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Bass Recipes
    {
        "id": "recipe-bass-1",
        "text": "Grilled Bass with Lemon Herb Butter: Score skin side of bass fillets. Season with salt and pepper. Grill skin-side down for 4-5 minutes, flip once. Serve with melted butter mixed with fresh dill, parsley, and lemon zest. Elegant and simple preparation.",
        "metadata": {
            "species": "largemouth_bass",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    {
        "id": "recipe-bass-2",
        "text": "Bass Po'Boy Sandwich: Cut bass into chunks, coat in seasoned cornmeal. Deep fry until crispy. Pile onto a French roll with shredded lettuce, pickles, and remoulade sauce. Classic Southern-style preparation that's hearty and satisfying.",
        "metadata": {
            "species": "largemouth_bass",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Trout Recipes
    {
        "id": "recipe-trout-1",
        "text": "Trout Almondine: Pan-fry trout fillets in butter until skin is crispy. Remove fish, add more butter to pan with slivered almonds. Toast almonds, add lemon juice and parsley. Pour over trout. Elegant French classic that's quick to prepare.",
        "metadata": {
            "species": "rainbow_trout",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    {
        "id": "recipe-trout-2",
        "text": "Whole Grilled Trout: Stuff cavity with lemon slices, fresh herbs (dill, thyme), and garlic. Rub outside with olive oil, salt, and pepper. Grill over medium heat 6-8 minutes per side. Fish is done when flesh flakes easily. Perfect campfire meal.",
        "metadata": {
            "species": "rainbow_trout",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Pike Recipes
    {
        "id": "recipe-pike-1",
        "text": "Pike Fish Cakes: Cook and flake pike, mix with mashed potatoes, chopped onion, parsley, and egg. Form into patties, coat in breadcrumbs. Pan-fry until golden brown on both sides. Serve with tartar sauce or aioli. Great way to use pike while managing Y-bones.",
        "metadata": {
            "species": "northern_pike",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    {
        "id": "recipe-pike-2",
        "text": "Baked Pike with Vegetables: Place pike fillets on bed of sliced potatoes, carrots, and onions in a baking dish. Season with salt, pepper, and herbs. Drizzle with olive oil and white wine. Bake at 400°F for 20-25 minutes until fish flakes. One-pan meal.",
        "metadata": {
            "species": "northern_pike",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Perch Recipes
    {
        "id": "recipe-perch-1",
        "text": "Classic Fried Perch: Small perch are perfect for pan-frying whole or as fillets. Dip in milk, then seasoned flour. Fry in hot oil until golden and crispy. Serve with lemon wedges and french fries. Traditional Friday fish fry style that's always a hit.",
        "metadata": {
            "species": "yellow_perch",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    {
        "id": "recipe-perch-2",
        "text": "Perch Ceviche: Cut fresh perch into small cubes. Marinate in lime juice with diced red onion, jalapeño, cilantro, and salt for 2-3 hours until fish is 'cooked' by acid. Serve cold with tortilla chips. Light and refreshing appetizer perfect for summer.",
        "metadata": {
            "species": "yellow_perch",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    # Salmon Recipes
    {
        "id": "recipe-salmon-1",
        "text": "Cedar Plank Salmon: Soak cedar plank for 2 hours. Place salmon fillet on plank, season with brown sugar, salt, and dill. Grill over indirect heat for 15-20 minutes. Wood imparts smoky flavor. Popular campfire or BBQ method that's impressive and delicious.",
        "metadata": {
            "species": "chinook_salmon",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    },
    {
        "id": "recipe-salmon-2",
        "text": "Pan-Seared Salmon with Dill Sauce: Season salmon fillets with salt and pepper. Sear skin-side down in hot pan for 4-5 minutes, flip and cook 2-3 minutes more. Serve with sauce of sour cream, fresh dill, lemon juice, and capers. Quick and elegant weeknight meal.",
        "metadata": {
            "species": "chinook_salmon",
            "spot": None,
            "region": "ontario",
            "type": "recipe",
            "risk_level": "edible",
            "risk_tags": [],
            "source": "DEMO"
        }
    }
]

# ============ COMMUNITY MEMORY ============
COMMUNITY_CHUNKS = [
    # Bayfront Park reports
    {
        "id": "community-bayfront-1",
        "text": "Bayfront Park - Algae bloom reported near shore. Water looks greenish. Be cautious if consuming fish caught here. Report from 3 days ago. Still present as of yesterday.",
        "metadata": {
            "species": None,
            "spot": "Bayfront Park",
            "region": "ontario",
            "type": "community",
            "risk_level": "caution",
            "risk_tags": ["algae_bloom"],
            "timestamp": (now - timedelta(days=3)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-bayfront-2",
        "text": "Bayfront Park - Great walleye bite this morning! Caught 3 keepers in 2 hours. Fishing near the breakwall. Parking lot full by 6am on weekends. Water clarity good.",
        "metadata": {
            "species": "walleye",
            "spot": "Bayfront Park",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(hours=6)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-bayfront-3",
        "text": "Bayfront Park - Ice conditions unsafe. Multiple reports of thin ice near the center. Wait for colder weather. As of last week, avoid ice fishing here.",
        "metadata": {
            "species": None,
            "spot": "Bayfront Park",
            "region": "ontario",
            "type": "community",
            "risk_level": "not_recommended",
            "risk_tags": ["unsafe_ice"],
            "timestamp": (now - timedelta(days=7)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-bayfront-4",
        "text": "Bayfront Park - Parking lot maintenance scheduled for next week. Alternative parking available 500m south at community center. Plan accordingly for weekend trips.",
        "metadata": {
            "species": None,
            "spot": "Bayfront Park",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": ["parking_closed"],
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-bayfront-5",
        "text": "Bayfront Park - Water temperature perfect for bass. Schools active near weed beds in shallow areas. Topwater lures working well in early morning. Great conditions today!",
        "metadata": {
            "species": "largemouth_bass",
            "spot": "Bayfront Park",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(hours=12)).isoformat(),
            "source": "DEMO"
        }
    },
    # Lake Simcoe reports
    {
        "id": "community-simcoe-1",
        "text": "Lake Simcoe - Parking lot closed for maintenance until next week. Alternative parking available 500m south at the community center. Plan accordingly for weekend trips.",
        "metadata": {
            "species": None,
            "spot": "Lake Simcoe",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": ["parking_closed"],
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-simcoe-2",
        "text": "Lake Simcoe - Excellent perch fishing! Schools of yellow perch active in 15-20 feet of water. Using minnows and small jigs. Limit catch within 2 hours yesterday. Great day out!",
        "metadata": {
            "species": "yellow_perch",
            "spot": "Lake Simcoe",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(hours=12)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-simcoe-3",
        "text": "Lake Simcoe - Water clarity excellent. Visibility about 10 feet. Bass are active near weed beds. Topwater lures working well in early morning. Report from yesterday. Perfect conditions.",
        "metadata": {
            "species": "largemouth_bass",
            "spot": "Lake Simcoe",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-simcoe-4",
        "text": "Lake Simcoe - Large pike caught near deep drop-offs. 15+ pounder released. Be careful handling - these fish are aggressive. Great catch and release spot. Respect the resource!",
        "metadata": {
            "species": "northern_pike",
            "spot": "Lake Simcoe",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(days=2)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-simcoe-5",
        "text": "Lake Simcoe - Water quality advisory lifted. Previous concerns about industrial runoff have been addressed. Safe for consumption following standard guidelines. Good news!",
        "metadata": {
            "species": None,
            "spot": "Lake Simcoe",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(days=5)).isoformat(),
            "source": "DEMO"
        }
    },
    # Rouge River reports
    {
        "id": "community-rouge-1",
        "text": "Rouge River - High water levels after recent rain. Current is strong, be careful wading. Fish are holding in slower eddies. Best fishing in pools behind large rocks. Exercise caution.",
        "metadata": {
            "species": "rainbow_trout",
            "spot": "Rouge River",
            "region": "ontario",
            "type": "community",
            "risk_level": "caution",
            "risk_tags": ["high_water"],
            "timestamp": (now - timedelta(days=2)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-rouge-2",
        "text": "Rouge River - Trout stocking completed last week. Stocked 500 rainbow trout near the dam. Should be good fishing in the coming days. Fish are adjusting to river conditions. Check regulations!",
        "metadata": {
            "species": "rainbow_trout",
            "spot": "Rouge River",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(days=5)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-rouge-3",
        "text": "Rouge River - Bridge construction upstream affecting water quality temporarily. Sediment in water. Fishing still possible but catch rates lower. Expected to clear in a week. Monitor conditions.",
        "metadata": {
            "species": None,
            "spot": "Rouge River",
            "region": "ontario",
            "type": "community",
            "risk_level": "caution",
            "risk_tags": ["water_quality"],
            "timestamp": (now - timedelta(days=4)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-rouge-4",
        "text": "Rouge River - Excellent salmon run right now! Chinook salmon moving upstream. Best time is early morning. Respect spawning fish and practice catch-and-release during spawning season.",
        "metadata": {
            "species": "chinook_salmon",
            "spot": "Rouge River",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "source": "DEMO"
        }
    },
    {
        "id": "community-rouge-5",
        "text": "Rouge River - Angler reports good walleye action in deeper pools. Using jigs and minnows. Fish are healthy and active. Great spot for evening fishing. Bring bug spray!",
        "metadata": {
            "species": "walleye",
            "spot": "Rouge River",
            "region": "ontario",
            "type": "community",
            "risk_level": "edible",
            "risk_tags": [],
            "timestamp": (now - timedelta(hours=18)).isoformat(),
            "source": "DEMO"
        }
    }
]


def main():
    print("=" * 60)
    print("GOFISH MOORCHEH BRAIN - SEED DATASET INGESTION")
    print("=" * 60)
    print(f"\nIngesting comprehensive dataset:")
    print(f"  - Safety chunks: {len(SAFETY_CHUNKS)}")
    print(f"  - Recipe chunks: {len(RECIPE_CHUNKS)}")
    print(f"  - Community chunks: {len(COMMUNITY_CHUNKS)}")
    print(f"\nNamespaces:")
    print(f"  - Safety: {NS_SAFETY}")
    print(f"  - Recipes: {NS_RECIPES}")
    print(f"  - Community: {NS_COMMUNITY}")
    print("\n" + "=" * 60 + "\n")
    
    client = GoFishMoorchehClient()
    
    # Create namespaces
    print("Creating namespaces...")
    client.create_namespace(NS_SAFETY, namespace_type="text")
    client.create_namespace(NS_RECIPES, namespace_type="text")
    client.create_namespace(NS_COMMUNITY, namespace_type="text")
    print()
    
    # Ingest safety chunks
    print(f"Ingesting {len(SAFETY_CHUNKS)} safety chunks into {NS_SAFETY}...")
    client.upload_documents(NS_SAFETY, SAFETY_CHUNKS, batch_size=50)
    print()
    
    # Ingest recipe chunks
    print(f"Ingesting {len(RECIPE_CHUNKS)} recipe chunks into {NS_RECIPES}...")
    client.upload_documents(NS_RECIPES, RECIPE_CHUNKS, batch_size=50)
    print()
    
    # Ingest community chunks
    print(f"Ingesting {len(COMMUNITY_CHUNKS)} community chunks into {NS_COMMUNITY}...")
    client.upload_documents(NS_COMMUNITY, COMMUNITY_CHUNKS, batch_size=50)
    print()
    
    print("=" * 60)
    print("SEED DATASET INGESTION COMPLETE!")
    print("=" * 60)
    print(f"\nTotal chunks ingested: {len(SAFETY_CHUNKS) + len(RECIPE_CHUNKS) + len(COMMUNITY_CHUNKS)}")
    print(f"  - Safety: {len(SAFETY_CHUNKS)} chunks")
    print(f"  - Recipes: {len(RECIPE_CHUNKS)} chunks")
    print(f"  - Community: {len(COMMUNITY_CHUNKS)} chunks")
    print("\nYour Moorcheh brain is ready to provide advice!")


if __name__ == "__main__":
    main()

