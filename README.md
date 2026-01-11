# GoFish Brain - Moorcheh Memory-in-a-Box

Community fishing assistant powered by Moorcheh's Memory-in-a-Box for evidence-based safety and recipe guidance.

## 🏆 Why Moorcheh is the Brain

Moorcheh isn't just a side feature—it's the **core intelligence layer** that makes GoFish work:

### 🧠 Multi-Namespace Memory Architecture
- **3 Dedicated Namespaces**: `safety_memory`, `recipe_memory`, `community_memory`
- Each namespace stores specialized knowledge with rich metadata
- Enables precise retrieval by species, spot, region, and risk factors

### 🔍 Semantic Search at Scale
- **Ingestion**: Efficiently binarizes and indexes safety advisories, recipes, and community reports
- **Retrieval**: Performs simultaneous multi-namespace searches with metadata filtering
- **Personalization**: Filters results based on user preferences (pregnancy, mercury sensitivity, etc.)

### 🎯 Evidence-Based Decision Making
- **No Hallucinations**: Our agent logic processes ONLY retrieved evidence
- **Transparent Labels**: Determines `EDIBLE` / `CAUTION` / `NOT_RECOMMENDED` / `UNKNOWN` based on actual safety chunks
- **Evidence Display**: Shows all retrieved snippets with scores so judges can verify grounding

### 🔄 Continuous Learning
- **Live Memory Updates**: Community posts are instantly ingested into Moorcheh
- **Real-Time Impact**: New reports immediately affect future queries
- **Persistent Memory**: Moorcheh's binarization ensures efficient storage and retrieval

### 📊 Unique Dataset
- **6 Fish Species**: Comprehensive safety and recipe data for walleye, pike, bass, trout, perch, salmon
- **3 Fishing Spots**: Community reports with timestamps and risk indicators
- **Rich Metadata**: Every chunk includes species, spot, region, risk_level, risk_tags for precise filtering

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Moorcheh API key

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up `.env` file:**
```
MOORCHEH_API_KEY=your_api_key_here
MOORCHEH_BASE_URL=https://api.moorcheh.ai
NS_SAFETY=safety_memory
NS_RECIPES=recipe_memory
NS_COMMUNITY=community_memory
```

3. **Ingest seed data:**
```bash
python scripts/ingest_seed_dataset.py
```

This will:
- Create 3 Moorcheh namespaces
- Ingest 39 chunks (12 safety + 12 recipes + 15 community)
- All chunks include proper metadata for filtering

4. **Start server:**
```bash
uvicorn app:app --reload
```

5. **Visit:** `http://localhost:8000`

## 📡 API Endpoints

### POST `/brain/advise`

Main brain endpoint - multi-namespace retrieval + evidence-based decision making.

**Request:**
```json
{
  "species": "walleye",
  "spot": "Bayfront Park",
  "preferences": {
    "avoid_high_mercury": true,
    "pregnant": false,
    "catch_and_release": false
  }
}
```

**Response:**
```json
{
  "species": "walleye",
  "spot": "Bayfront Park",
  "edibility_label": "EDIBLE",
  "safety_summary": [
    "Walleye from Ontario waters are generally safe...",
    "Keep fish cold on ice immediately after catch...",
    "Limit consumption to 2-4 meals per month..."
  ],
  "recipes": [
    {
      "title": "Classic Pan-Fried Walleye",
      "steps": ["Season fillets...", "Dredge in flour...", "Pan-fry..."],
      "source_snippet": "..."
    }
  ],
  "community_alerts": [
    "Great walleye bite this morning! Caught 3 keepers...",
    "Algae bloom reported near shore..."
  ],
  "evidence": {
    "safety": [
      {
        "text": "...",
        "score": 0.87,
        "metadata": {"species": "walleye", "risk_level": "edible", ...},
        "namespace": "safety_memory"
      }
    ],
    "recipes": [...],
    "community": [...]
  }
}
```

### POST `/memory/ingestCommunity`

Ingest a new community report into Moorcheh memory (proves live updates).

**Request:**
```json
{
  "spot": "Lake Simcoe",
  "handle": "@angler123",
  "text": "Great perch fishing today! Caught 10 keepers."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Community report ingested into Moorcheh memory",
  "document_id": "community-1234567890"
}
```

### GET `/health`

Health check endpoint.

## 🎨 Frontend Features

The polished demo UI includes:

- **Species Selection**: Dropdown with 6 fish species
- **Spot Selection**: Optional fishing location
- **Preference Toggles**: Avoid high mercury, pregnant, catch & release
- **Edibility Badge**: Large, color-coded label (EDIBLE/CAUTION/NOT_RECOMMENDED/UNKNOWN)
- **Tabbed Interface**: Safety | Recipes | Community
- **Evidence Transparency**: Collapsible section showing all retrieved snippets with scores
- **Community Report Form**: Post new reports that instantly update Moorcheh memory

## 🔬 How Evidence-Based Decision Making Works

Our agent logic (NO LLM) determines edibility labels using these rules:

1. **NOT_RECOMMENDED** if:
   - Any safety chunk has `risk_level="not_recommended"`
   - Pregnancy caution tags when `pregnant=true`

2. **CAUTION** if:
   - Any safety chunk has `risk_level="caution"`
   - High mercury tags when `avoid_high_mercury=true`
   - Community reports indicate caution

3. **EDIBLE** if:
   - At least one safety chunk has `risk_level="edible"`
   - No blocking factors present

4. **UNKNOWN** if:
   - No safety chunks retrieved

All decisions are **transparent** - the evidence section shows exactly which snippets were used.

## 📊 Dataset Statistics

- **6 Fish Species**: walleye, largemouth_bass, rainbow_trout, northern_pike, yellow_perch, chinook_salmon
- **12 Safety Chunks**: 2 per species (edibility + handling)
- **12 Recipe Chunks**: 2 per species (cooking methods)
- **15 Community Reports**: 5 per spot across 3 locations
- **39 Total Chunks**: All with rich metadata for filtering

## 🏗️ Architecture

```
Fish Species Identified (String Input)
                ↓
         GoFish Brain API
                ↓
    ┌───────────┼───────────┐
    │           │           │
Moorcheh    Moorcheh    Moorcheh
Safety      Recipes     Community
Memory      Memory      Memory
    │           │           │
    └───────────┼───────────┘
                ↓
        Agent Logic (Evidence-Based)
                ↓
    EDIBLE / CAUTION / NOT_RECOMMENDED
    + Safety Summary + Recipes + Alerts
```

## 📝 Notes

- **No MongoDB**: This system uses Moorcheh only for text storage and retrieval
- **No CV**: Fish species identification is handled elsewhere
- **No LLM**: All summaries and decisions come from retrieved evidence only
- **Demo Data**: All seed data is clearly labeled as "DEMO"

---

**Built for the Moorcheh "Best Use of Memory-in-a-Box" hackathon** 🏆
