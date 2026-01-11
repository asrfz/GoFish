"use client";

import { useState, useEffect, useRef } from "react";
import { MapPin, Search, Loader2, Thermometer, Droplets, Navigation } from "lucide-react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FishingSpot {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  bite_score: number;
  status: string;
  reasoning: string;
  weather: {
    temperature: number;
    pressure: number;
    wind_speed: number;
  };
}

interface BestSpotsPostProps {
  onSpotFound?: (data: any) => void;
}

export default function BestSpotsPost({ onSpotFound }: BestSpotsPostProps) {
  const [location, setLocation] = useState("");
  const [species, setSpecies] = useState("walleye");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bestSpot, setBestSpot] = useState<FishingSpot | null>(null);
  const [spots, setSpots] = useState<FishingSpot[]>([]);
  const [supportedSpecies, setSupportedSpecies] = useState<string[]>([]);
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  // Load cached search on mount
  useEffect(() => {
    const cachedSearch = localStorage.getItem("gofish_spots_search");
    if (cachedSearch) {
      try {
        const parsed = JSON.parse(cachedSearch);
        setLocation(parsed.location || "");
        setSpecies(parsed.species || "walleye");
        if (parsed.spots && parsed.spots.length > 0) {
          setSpots(parsed.spots);
          setBestSpot(parsed.bestSpot || parsed.spots[0] || null);
          // Restore map markers
          setTimeout(() => {
            if (parsed.spots.length > 0) {
              updateMapMarkers(parsed.spots);
            }
          }, 500);
        }
      } catch (e) {
        console.error("Failed to load cached search:", e);
      }
    }
  }, []);

  // Cache search results
  const cacheSearch = (searchLocation: string, searchSpecies: string, searchSpots: FishingSpot[], searchBest: FishingSpot | null) => {
    localStorage.setItem("gofish_spots_search", JSON.stringify({
      location: searchLocation,
      species: searchSpecies,
      spots: searchSpots,
      bestSpot: searchBest,
      timestamp: Date.now(),
    }));
  };

  useEffect(() => {
    const fetchSpecies = async () => {
      try {
        const response = await fetch(`${API_URL}/api/species`);
        const data = await response.json();
        setSupportedSpecies(data.species || []);
      } catch (err) {
        console.error("Failed to fetch species:", err);
      }
    };
    fetchSpecies();
    initializeMap();
    
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  const initializeMap = () => {
    if (map.current || !mapContainer.current) {
      // Retry if container not ready
      if (!mapContainer.current) {
        setTimeout(() => initializeMap(), 100);
      }
      return;
    }

    try {
      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: "https://tiles.openfreemap.org/styles/dark",
        center: [-79.5, 44.0],
        zoom: 6,
        attributionControl: false,
      });

      map.current.addControl(new maplibregl.NavigationControl(), "top-right");
      map.current.addControl(
        new maplibregl.AttributionControl({ compact: true }),
        "bottom-right"
      );

      map.current.on("load", () => {
        console.log("Map loaded successfully");
        // Update markers if spots already loaded
        if (spots.length > 0) {
          updateMapMarkers(spots);
        }
      });

      map.current.on("error", (e) => {
        console.error("Map error:", e);
      });
    } catch (error) {
      console.error("Failed to initialize map:", error);
    }
  };

  const updateMapMarkers = (spotsData: FishingSpot[]) => {
    if (!map.current || !spotsData.length) {
      // If map not ready, wait for it
      if (map.current && !map.current.loaded()) {
        map.current.once("load", () => updateMapMarkers(spotsData));
        return;
      }
      setTimeout(() => updateMapMarkers(spotsData), 100);
      return;
    }
    
    if (!map.current.loaded()) {
      map.current.once("load", () => updateMapMarkers(spotsData));
      return;
    }

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    spotsData.slice(0, 50).forEach((spot) => {
      const score = spot.bite_score;
      const color =
        score >= 75 ? "#22c55e" : score >= 55 ? "#eab308" : score >= 35 ? "#f97316" : "#ef4444";

      const el = document.createElement("div");
      el.className = "spot-marker";
      el.style.cssText = `
        width: 32px;
        height: 32px;
        background: radial-gradient(circle, ${color}dd 0%, ${color}44 70%, transparent 100%);
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 10px;
        color: white;
        text-shadow: 0 1px 2px rgba(0,0,0,0.8);
        box-shadow: 0 0 15px ${color}66;
      `;
      el.textContent = score.toString();

      const popup = new maplibregl.Popup({ offset: 25, closeButton: false }).setHTML(`
        <div style="background: #1e293b; color: white; padding: 12px; border-radius: 8px; min-width: 200px;">
          <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">${spot.name}</h3>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #94a3b8;">Score:</span>
            <span style="color: ${color}; font-weight: 600;">${score}/100</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #94a3b8;">Status:</span>
            <span>${spot.status}</span>
          </div>
          <p style="margin: 8px 0 0 0; font-size: 11px; color: #94a3b8;">${spot.reasoning}</p>
        </div>
      `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([spot.longitude, spot.latitude])
        .setPopup(popup)
        .addTo(map.current);

      el.onclick = () => setBestSpot(spot);
      markersRef.current.push(marker);
    });

    if (spotsData.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      spotsData.slice(0, 10).forEach((spot) => {
        bounds.extend([spot.longitude, spot.latitude]);
      });
      map.current.fitBounds(bounds, { padding: 50 });
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setBestSpot(null);

    try {
      let bounds = "";

      if (location.trim()) {
        try {
          const geoResponse = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(location + ", Ontario, Canada")}&format=json&limit=1`
          );
          const geoData = await geoResponse.json();

          if (geoData.length > 0) {
            const { boundingbox } = geoData[0];
            if (boundingbox) {
              const [minLat, maxLat, minLon, maxLon] = boundingbox;
              bounds = `&min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}`;
            }
          }
        } catch (geoError) {
          console.log("Geocoding failed:", geoError);
        }
      }

      // Check backend connectivity first
      let healthOk = false;
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        const healthCheck = await fetch(`${API_URL}/api/health`, { 
          method: "GET",
          signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (!healthCheck.ok) {
          throw new Error("Backend health check failed");
        }
        healthOk = true;
      } catch (healthError) {
        if (healthError instanceof Error && healthError.name === 'AbortError') {
          throw new Error(`Backend timeout. Make sure the backend server is running on port 8000 at ${API_URL}`);
        }
        throw new Error(`Cannot connect to backend at ${API_URL}. Make sure the backend server is running: python app.py`);
      }

      const controller2 = new AbortController();
      const timeoutId2 = setTimeout(() => controller2.abort(), 15000);
      const response = await fetch(
        `${API_URL}/api/fishing-spots?species=${species}&limit=50${bounds}`,
        {
          signal: controller2.signal
        }
      );
      clearTimeout(timeoutId2);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error (${response.status}): ${errorText || response.statusText}`);
      }

      const data = await response.json();
      const spotsData = data.spots || [];
      setSpots(spotsData);
      if (spotsData.length > 0) {
        const topSpot = spotsData[0];
        setBestSpot(topSpot);
        updateMapMarkers(spotsData);
        // Cache the search results
        cacheSearch(location, species, spotsData, topSpot);
        if (onSpotFound) {
          onSpotFound({
            type: "spot",
            data: {
              name: topSpot.name,
              bite_score: topSpot.bite_score,
              reasoning: topSpot.reasoning,
            },
          });
        }
      } else {
        throw new Error("No fishing spots found for this species. Try a different species.");
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to fetch fishing spots";
      if (errorMessage.includes("abort") || errorMessage.includes("timeout")) {
        setError(`⏱️ Request timed out. Backend may be slow or not responding.`);
      } else if (errorMessage.includes("fetch") || errorMessage.includes("connect")) {
        setError(`🔌 Cannot connect to backend at ${API_URL}\n\nMake sure:\n1. Backend is running: python app.py\n2. Backend is on port 8000\n3. Check terminal for errors`);
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Great":
        return "text-emerald-600 bg-emerald-50";
      case "Good":
        return "text-yellow-600 bg-yellow-50";
      case "Fair":
        return "text-orange-600 bg-orange-50";
      default:
        return "text-red-600 bg-red-50";
    }
  };

  return (
    <div className="bg-white">
      {/* Post Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <MapPin className="w-5 h-5" />
          Find Best Fishing Spots
        </h2>
        <p className="text-xs text-gray-500 mt-1">Discover top locations with real-time bite scores</p>
      </div>

      {/* Search Section */}
      <div className="p-4 space-y-3 bg-gray-50">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Location (optional)
          </label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g., Muskoka, Ottawa..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Target Species</label>
          <select
            value={species}
            onChange={(e) => setSpecies(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {supportedSpecies.length > 0 ? (
              supportedSpecies.map((s) => (
                <option key={s} value={s}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </option>
              ))
            ) : (
              <>
                <option value="walleye">Walleye</option>
                <option value="bass">Bass</option>
                <option value="trout">Trout</option>
                <option value="pike">Pike</option>
                <option value="perch">Perch</option>
              </>
            )}
          </select>
        </div>

        <button
          onClick={handleSearch}
          disabled={loading}
          className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white font-semibold py-3 rounded-lg transition flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Find Best Spots
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 m-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700 whitespace-pre-line">{error}</p>
        </div>
      )}

      {/* Results Section */}
          {/* Map View */}
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="mb-2">
              <p className="text-sm font-semibold text-gray-700 mb-1">Map View</p>
              <p className="text-xs text-gray-500">
                {spots.length > 0 ? `${spots.length} spots found` : "Search for spots to see them on the map"}
              </p>
            </div>
            <div
              ref={mapContainer}
              className="w-full rounded-lg overflow-hidden border border-gray-300 bg-gray-200"
              style={{ height: "400px", minHeight: "400px" }}
            />
          </div>

          {bestSpot && (
        <div className="p-4 space-y-4 border-t border-gray-200">
          <div className="flex items-center gap-2 text-blue-600 text-sm font-medium mb-2">
            <Navigation className="w-4 h-4" />
            BEST SPOT FOR {species.toUpperCase()}
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-4 border border-blue-200">
            <h3 className="text-xl font-bold text-gray-900 mb-2">{bestSpot.name}</h3>

            <div className="flex items-center gap-3 mb-3">
              <div className={`px-3 py-1.5 rounded-full font-bold ${getStatusColor(bestSpot.status)}`}>
                {bestSpot.bite_score}/100
              </div>
              <span className={`text-sm font-semibold ${getStatusColor(bestSpot.status).split(' ')[0]}`}>
                {bestSpot.status} Conditions
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="bg-white/60 rounded-lg p-2 text-center">
                <Thermometer className="w-4 h-4 text-orange-500 mx-auto mb-1" />
                <p className="text-xs text-gray-600">{bestSpot.weather.temperature}°C</p>
              </div>
              <div className="bg-white/60 rounded-lg p-2 text-center">
                <Droplets className="w-4 h-4 text-blue-500 mx-auto mb-1" />
                <p className="text-xs text-gray-600">{bestSpot.weather.pressure.toFixed(0)} hPa</p>
              </div>
              <div className="bg-white/60 rounded-lg p-2 text-center">
                <p className="text-xs text-gray-600">{bestSpot.weather.wind_speed.toFixed(0)} km/h</p>
              </div>
            </div>

            <p className="text-xs text-gray-700 bg-white/60 rounded p-2">
              <strong>Why here?</strong> {bestSpot.reasoning}
            </p>

            <p className="text-xs text-gray-500 mt-2">
              📍 {bestSpot.latitude.toFixed(4)}°N, {Math.abs(bestSpot.longitude).toFixed(4)}°W
            </p>
          </div>

          {spots.length > 1 && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-2">
                Showing top spot of {spots.length} results
              </p>
              <div className="flex flex-wrap gap-2">
                {spots.slice(1, 4).map((spot, idx) => (
                  <button
                    key={`${spot.id}-${idx}-${spot.latitude}-${spot.longitude}`}
                    onClick={() => setBestSpot(spot)}
                    className="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-700 hover:bg-gray-50"
                  >
                    {spot.name} ({spot.bite_score})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
