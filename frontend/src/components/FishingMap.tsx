"use client";

import { useEffect, useRef, useState } from "react";
import { MapPin, Loader } from "lucide-react";

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

export default function FishingMap() {
    const [species, setSpecies] = useState("walleye");
    const [spots, setSpots] = useState<FishingSpot[]>([]);
    const [loading, setLoading] = useState(false);
    const [supportedSpecies, setSupportedSpecies] = useState<string[]>([]);
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<any>(null);

    // Fetch supported species
    useEffect(() => {
        const fetchSpecies = async () => {
            try {
                const response = await fetch(`${API_URL}/api/species`);
                const data = await response.json();
                setSupportedSpecies(data.species);
            } catch (err) {
                console.error("Failed to fetch species:", err);
            }
        };
        fetchSpecies();
    }, []);

    // Fetch fishing spots
    const fetchSpots = async (selectedSpecies: string) => {
        try {
            setLoading(true);
            const response = await fetch(
                `${API_URL}/api/fishing-spots?species=${selectedSpecies}&limit=50`
            );
            const data = await response.json();
            setSpots(data.spots);
        } catch (err) {
            console.error("Failed to fetch spots:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSpots(species);
    }, [species]);

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <MapPin className="w-6 h-6 text-blue-600" />
                    Find Fishing Spots
                </h2>
                <div className="flex gap-4">
                    <div className="flex-1">
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                            Select Species:
                        </label>
                        <select
                            value={species}
                            onChange={(e) => setSpecies(e.target.value)}
                            disabled={loading}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600 disabled:bg-gray-100"
                        >
                            {supportedSpecies.map((sp) => (
                                <option key={sp} value={sp}>
                                    {sp.charAt(0).toUpperCase() + sp.slice(1)}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="flex items-end">
                        <button
                            onClick={() => fetchSpots(species)}
                            disabled={loading}
                            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold rounded-lg transition"
                        >
                            {loading ? <Loader className="w-5 h-5 animate-spin" /> : "Search"}
                        </button>
                    </div>
                </div>
            </div>

            {/* Results */}
            {spots.length > 0 && (
                <div className="grid md:grid-cols-2 gap-6">
                    {/* Map Placeholder */}
                    <div
                        ref={mapContainer}
                        className="bg-white rounded-lg shadow-lg overflow-hidden h-96 border-2 border-gray-200 flex items-center justify-center"
                    >
                        <div className="text-center text-gray-500">
                            <p className="font-semibold">Map View</p>
                            <p className="text-sm">{spots.length} spots found</p>
                            <p className="text-xs mt-2">Showing {species} fishing locations</p>
                        </div>
                    </div>

                    {/* Spots List */}
                    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                        <div className="bg-gradient-to-r from-blue-500 to-cyan-600 p-4">
                            <h3 className="text-white font-bold">
                                Top Spots for {species.toUpperCase()}
                            </h3>
                            <p className="text-blue-100 text-sm">{spots.length} locations</p>
                        </div>
                        <div className="overflow-y-auto h-96 divide-y">
                            {spots.slice(0, 10).map((spot, idx) => (
                                <div key={spot.id} className="p-4 hover:bg-gray-50 transition">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <p className="font-bold text-gray-900">
                                                #{idx + 1} - {spot.name}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {spot.latitude.toFixed(3)}, {spot.longitude.toFixed(3)}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-2xl font-bold text-orange-600">
                                                {spot.bite_score}
                                            </p>
                                            <p className="text-xs font-semibold text-gray-600">
                                                {spot.status}
                                            </p>
                                        </div>
                                    </div>
                                    <p className="text-xs text-gray-600 mb-2">{spot.reasoning}</p>
                                    <div className="grid grid-cols-3 gap-2 text-xs">
                                        <div className="bg-blue-50 p-2 rounded">
                                            <p className="text-gray-600">Temp</p>
                                            <p className="font-semibold">{spot.weather.temperature}°C</p>
                                        </div>
                                        <div className="bg-purple-50 p-2 rounded">
                                            <p className="text-gray-600">Pressure</p>
                                            <p className="font-semibold">{spot.weather.pressure} mb</p>
                                        </div>
                                        <div className="bg-green-50 p-2 rounded">
                                            <p className="text-gray-600">Wind</p>
                                            <p className="font-semibold">{spot.weather.wind_speed} km/h</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {loading && (
                <div className="text-center py-12">
                    <Loader className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-2" />
                    <p className="text-gray-600">Loading fishing spots...</p>
                </div>
            )}

            {!loading && spots.length === 0 && (
                <div className="bg-gray-100 rounded-lg p-12 text-center">
                    <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-700 font-semibold">No spots found</p>
                    <p className="text-gray-600 text-sm">Try selecting a different species</p>
                </div>
            )}
        </div>
    );

                        // Add fill layer with score-based coloring
                        map.current!.addLayer({
                            id: "habitat-fill",
                            type: "fill",
                            source: "habitats",
                            paint: {
                                "fill-color": [
                                    "interpolate",
                                    ["linear"],
                                    ["coalesce", ["get", "potential_score_capped"], 0],
                                    0, "#c7e9c0",           // Very low - light green
                                    quantiles.q20, "#a1d99b",
                                    quantiles.q40, "#74c476",
                                    quantiles.q60, "#31a354",
                                    quantiles.q80, "#006d2c", // High - dark green
                                    1, "#004d1a",             // Very high
                                ],
                                "fill-opacity": 0.65,
                            },
                        });

                        // Add outline layer
                        map.current!.addLayer({
                            id: "habitat-outline",
                            type: "line",
                            source: "habitats",
                            paint: {
                                "line-color": "#1a1a1a",
                                "line-width": 0.5,
                            },
                        });

                        // Add click handler for popups
                        map.current!.on("click", "habitat-fill", (e) => {
                            if (!e.features || e.features.length === 0) return;

                            const props = e.features[0].properties;
                            const score = props.potential_score_capped?.toFixed(3) || "N/A";
                            const lakeName = props.LAKE_NAME || "Unknown Waterbody";
                            const habitat = props.HABITAT_FE || "Unknown";
                            const area = props.AREA ? (props.AREA / 1000000).toFixed(2) + " km²" : "N/A";

                            new maplibregl.Popup({ closeButton: true })
                                .setLngLat(e.lngLat)
                                .setHTML(`
                  <div style="background: #1e293b; color: white; padding: 12px; border-radius: 8px; min-width: 200px;">
                    <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">${lakeName}</h3>
                    <div style="font-size: 12px; color: #94a3b8;">
                      <div style="margin-bottom: 4px;">Habitat: <span style="color: white;">${habitat}</span></div>
                      <div style="margin-bottom: 4px;">Score: <span style="color: #22c55e; font-weight: 600;">${score}</span></div>
                      <div>Area: <span style="color: white;">${area}</span></div>
                    </div>
                  </div>
                `)
                                .addTo(map.current!);
                        });

                        // Change cursor on hover
                        map.current!.on("mouseenter", "habitat-fill", () => {
                            map.current!.getCanvas().style.cursor = "pointer";
                        });
                        map.current!.on("mouseleave", "habitat-fill", () => {
                            map.current!.getCanvas().style.cursor = "";
                        });
                    }
                }
            } catch (error) {
                console.error("Error fetching habitat data:", error);
            }

            // Add station markers on top
            stations.forEach((station) => {
                const isRecommended = station.station_id === recommended?.station_id;
                const score = station.bite_scores[0]?.score || 50;

                const el = document.createElement("div");
                el.style.cssText = `
          width: ${isRecommended ? 44 : 28}px;
          height: ${isRecommended ? 44 : 28}px;
          background: ${isRecommended
                        ? "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)"
                        : "rgba(30, 41, 59, 0.95)"};
          border: 3px solid ${isRecommended ? "#fff" : "#475569"};
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: ${isRecommended ? 13 : 10}px;
          color: white;
          cursor: pointer;
          box-shadow: ${isRecommended
                        ? "0 0 20px rgba(16, 185, 129, 0.6)"
                        : "0 2px 8px rgba(0,0,0,0.4)"};
        `;
                el.textContent = score.toString();

                new maplibregl.Marker({ element: el })
                    .setLngLat([station.longitude, station.latitude])
                    .addTo(map.current!);
            });
        });

        return () => {
            map.current?.remove();
            map.current = null;
        };
    }, [stations, recommended]);

    return (
        <div className="w-full h-full rounded-2xl overflow-hidden border border-slate-700/50">
            <div ref={mapContainer} className="w-full h-full" />
        </div>
    );
}
