"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Fish, MapPin, Search, Loader2, Navigation, Droplets, Thermometer, TrendingUp, Map, Trees } from "lucide-react";

const ResultMap = dynamic(() => import("@/components/FishingMap"), { ssr: false });

interface FishingSpot {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  potential_score: number;
  habitat_type: string;
  habitat_desc: string;
  area: number;
  weather: {
    temperature: number;
    pressure: number;
    wind_speed: number;
  };
  bite_score: number;
  status: string;
  reasoning: string;
}

export default function Home() {
  const [location, setLocation] = useState("");
  const [species, setSpecies] = useState("walleye");
  const [loading, setLoading] = useState(false);
  const [bestSpot, setBestSpot] = useState<FishingSpot | null>(null);
  const [allSpots, setAllSpots] = useState<FishingSpot[]>([]);
  const [totalSpots, setTotalSpots] = useState(0);

  const handleSearch = async () => {
    setLoading(true);
    setBestSpot(null);

    try {
      let bounds = "";

      // Geocode location if provided
      if (location.trim()) {
        try {
          const geoResponse = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(location + ", Ontario, Canada")}&format=json&limit=1`
          );
          const geoData = await geoResponse.json();

          if (geoData.length > 0) {
            const { lat, lon, boundingbox } = geoData[0];
            // Use bounding box if available, otherwise create one around the point
            if (boundingbox) {
              const [minLat, maxLat, minLon, maxLon] = boundingbox;
              bounds = `&min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}`;
            } else {
              // Create a ~50km bounding box around the point
              bounds = `&min_lat=${parseFloat(lat) - 0.5}&max_lat=${parseFloat(lat) + 0.5}&min_lon=${parseFloat(lon) - 0.5}&max_lon=${parseFloat(lon) + 0.5}`;
            }
          }
        } catch (geoError) {
          console.log("Geocoding failed, showing all spots:", geoError);
        }
      }

      const response = await fetch(
        `http://localhost:8000/api/fishing-spots?species=${species}&limit=50${bounds}`
      );

      if (response.ok) {
        const data = await response.json();
        setAllSpots(data.spots);
        setTotalSpots(data.total_spots);
        if (data.spots.length > 0) {
          setBestSpot(data.spots[0]);
        }
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Great": return "text-emerald-400 bg-emerald-500/20";
      case "Good": return "text-yellow-400 bg-yellow-500/20";
      case "Fair": return "text-orange-400 bg-orange-500/20";
      default: return "text-red-400 bg-red-500/20";
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-3">
            <div className="p-3 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-2xl shadow-lg shadow-emerald-500/25">
              <Fish className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-white">Ontario Angler Pro</h1>
          </div>
          <p className="text-slate-400 text-lg">Find the best fishing spot from 15,000+ Ontario habitats</p>
        </div>

        {/* Search Card */}
        <div className="max-w-xl mx-auto bg-slate-800/50 backdrop-blur-xl rounded-3xl border border-slate-700/50 p-6 shadow-2xl mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                <MapPin className="w-4 h-4 inline mr-2" />
                Location (optional)
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., Muskoka, Ottawa..."
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                <Fish className="w-4 h-4 inline mr-2" />
                Target Species
              </label>
              <select
                value={species}
                onChange={(e) => setSpecies(e.target.value)}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all cursor-pointer"
              >
                <option value="walleye">🐟 Walleye</option>
                <option value="bass">🐟 Bass</option>
                <option value="trout">🐟 Trout</option>
                <option value="pike">🐟 Pike</option>
                <option value="perch">🐟 Perch</option>
              </select>
            </div>
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-lg shadow-emerald-500/25"
          >
            {loading ? (
              <><Loader2 className="w-5 h-5 animate-spin" /> Searching habitats...</>
            ) : (
              <><Search className="w-5 h-5" /> Find Best Fishing Spot</>
            )}
          </button>
        </div>

        {/* Results Section */}
        {bestSpot && allSpots.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Map */}
            <div className="order-2 lg:order-1">
              <div className="flex items-center justify-between text-slate-400 text-sm mb-3">
                <div className="flex items-center gap-2">
                  <Map className="w-4 h-4" />
                  <span>Top 50 Fishing Habitats</span>
                </div>
                <span className="text-xs text-slate-500">{totalSpots.toLocaleString()} total in database</span>
              </div>
              <div className="h-[400px] lg:h-[500px]">
                <ResultMap
                  stations={allSpots.map(s => ({
                    station_id: s.id,
                    station_name: s.name,
                    latitude: s.latitude,
                    longitude: s.longitude,
                    discharge: s.area,
                    weather: s.weather,
                    bite_scores: [{ species, score: s.bite_score, status: s.status }]
                  }))}
                  recommended={bestSpot ? {
                    station_id: bestSpot.id,
                    station_name: bestSpot.name,
                    latitude: bestSpot.latitude,
                    longitude: bestSpot.longitude,
                    discharge: bestSpot.area,
                    weather: bestSpot.weather,
                    bite_scores: [{ species, score: bestSpot.bite_score, status: bestSpot.status }]
                  } : null}
                />
              </div>
              <div className="flex items-center justify-center gap-6 mt-3 text-xs text-slate-500">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-blue-500" /> Cold
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-cyan-500" /> Cool
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-green-500" /> Mild
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-yellow-500" /> Warm
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-red-500" /> Hot
                </div>
              </div>
            </div>

            {/* Result Card */}
            <div className="order-1 lg:order-2">
              <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur-xl rounded-3xl border border-emerald-500/30 p-6 shadow-2xl shadow-emerald-500/10">
                <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium mb-4">
                  <Navigation className="w-4 h-4" />
                  BEST SPOT FOR {species.toUpperCase()}
                </div>

                <h2 className="text-2xl font-bold text-white mb-2">{bestSpot.name}</h2>

                <div className="flex items-center gap-4 mb-4">
                  <div className={`px-4 py-2 rounded-full font-bold text-xl ${getStatusColor(bestSpot.status)}`}>
                    {bestSpot.bite_score}/100
                  </div>
                  <span className={`font-semibold ${getStatusColor(bestSpot.status).split(' ')[0]}`}>
                    {bestSpot.status} Conditions
                  </span>
                </div>

                {/* Habitat Info */}
                <div className="bg-slate-800/50 rounded-xl p-4 mb-4">
                  <div className="flex items-center gap-2 text-slate-300 mb-2">
                    <Trees className="w-4 h-4 text-green-400" />
                    <span className="text-sm font-medium">Habitat Type</span>
                  </div>
                  <p className="text-sm text-slate-400">{bestSpot.habitat_type || "Fish habitat"}</p>
                  {bestSpot.habitat_desc && (
                    <p className="text-xs text-slate-500 mt-1">{bestSpot.habitat_desc}</p>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                    <Droplets className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                    <p className="text-lg font-semibold text-white">{(bestSpot.area / 1000).toFixed(1)}k</p>
                    <p className="text-xs text-slate-500">m² area</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                    <Thermometer className="w-5 h-5 text-orange-400 mx-auto mb-1" />
                    <p className="text-lg font-semibold text-white">{bestSpot.weather.temperature}°C</p>
                    <p className="text-xs text-slate-500">temp</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                    <TrendingUp className="w-5 h-5 text-purple-400 mx-auto mb-1" />
                    <p className="text-lg font-semibold text-white">{bestSpot.weather.pressure.toFixed(0)}</p>
                    <p className="text-xs text-slate-500">hPa</p>
                  </div>
                </div>

                <div className="bg-emerald-900/20 border border-emerald-500/20 rounded-xl p-4 mb-4">
                  <p className="text-sm text-emerald-300">
                    <strong>Why here?</strong> {bestSpot.reasoning}
                  </p>
                </div>

                <div className="bg-slate-800/30 rounded-xl p-3">
                  <p className="text-xs text-slate-400 mb-1">📍 Coordinates</p>
                  <p className="text-sm font-mono text-white">
                    {bestSpot.latitude.toFixed(4)}°N, {Math.abs(bestSpot.longitude).toFixed(4)}°W
                  </p>
                </div>

                {allSpots.length > 1 && (
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <p className="text-xs text-slate-500 mb-2">Other top spots:</p>
                    <div className="flex flex-wrap gap-2">
                      {allSpots
                        .filter(s => s.id !== bestSpot.id)
                        .slice(0, 4)
                        .map((s, index) => (
                          <button
                            key={`${s.id}-${index}`}
                            onClick={() => setBestSpot(s)}
                            className="px-3 py-1.5 bg-slate-700/50 hover:bg-slate-600/50 rounded-lg text-xs text-slate-300 transition-colors"
                          >
                            {s.name} ({s.bite_score})
                          </button>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <p className="mt-8 text-center text-xs text-slate-600">
          Data: Ontario Fish Habitat GeoJSON • Weather: Open-Meteo
        </p>
      </div>
    </main>
  );
}
