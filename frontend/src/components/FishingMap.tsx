"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

interface Station {
    station_id: string;
    station_name: string;
    latitude: number;
    longitude: number;
    discharge: number | null;
    weather: {
        temperature: number;
        pressure: number;
        wind_speed: number;
    };
    bite_scores: Array<{
        species: string;
        score: number;
        status: string;
    }>;
}

interface HabitatData {
    type: string;
    features: Array<{
        type: string;
        properties: {
            LAKE_NAME?: string;
            HABITAT_FE?: string;
            potential_score_capped?: number;
            AREA?: number;
        };
        geometry: {
            type: string;
            coordinates: number[][][];
        };
    }>;
    meta?: {
        quantiles: {
            q20: number;
            q40: number;
            q60: number;
            q80: number;
        };
    };
}

interface ResultMapProps {
    stations: Station[];
    recommended: Station | null;
}

export default function ResultMap({ stations, recommended }: ResultMapProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);

    useEffect(() => {
        if (!mapContainer.current) return;

        if (map.current) {
            map.current.remove();
            map.current = null;
        }

        const centerLat = recommended?.latitude || 44.5;
        const centerLon = recommended?.longitude || -79.5;

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: "https://tiles.openfreemap.org/styles/dark",
            center: [centerLon, centerLat],
            zoom: 7,
            attributionControl: false,
        });

        map.current.addControl(
            new maplibregl.NavigationControl({ showCompass: false }),
            "top-right"
        );

        map.current.on("load", async () => {
            if (!map.current) return;

            // Fetch habitat polygons from backend
            try {
                const response = await fetch("http://localhost:8000/api/fishing-habitats?limit=1000&min_score=0.3");
                if (response.ok) {
                    const habitatData: HabitatData = await response.json();

                    if (habitatData.features && habitatData.features.length > 0) {
                        const quantiles = habitatData.meta?.quantiles || { q20: 0.2, q40: 0.4, q60: 0.6, q80: 0.8 };

                        // Add habitat source
                        map.current!.addSource("habitats", {
                            type: "geojson",
                            data: habitatData as GeoJSON.FeatureCollection,
                        });

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
