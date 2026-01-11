"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

interface StationData {
    station_id: string;
    station_name: string;
    latitude: number;
    longitude: number;
    discharge: number | null;
    water_level: number | null;
    weather: {
        temperature: number;
        pressure: number;
        wind_speed: number;
        is_pressure_falling: boolean;
    };
    bite_scores: Array<{
        species: string;
        score: number;
        status: string;
        reasoning: string;
    }>;
}

interface FishingSpot {
    type: "Feature";
    properties: {
        OFFICIAL_NAME?: string;
        ACCESS_TYPE?: string;
    };
    geometry: {
        type: "Point";
        coordinates: [number, number];
    };
}

interface MapProps {
    selectedSpecies: string;
    onStationSelect: (station: StationData | null) => void;
}

export default function Map({ selectedSpecies, onStationSelect }: MapProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);
    const [stations, setStations] = useState<StationData[]>([]);
    const markersRef = useRef<maplibregl.Marker[]>([]);

    const fetchData = useCallback(async () => {
        try {
            const [forecastRes, spotsRes] = await Promise.all([
                fetch(`http://localhost:8000/api/bite-forecast${selectedSpecies ? `?species=${selectedSpecies}` : ""}`),
                fetch("http://localhost:8000/api/fishing-spots"),
            ]);

            if (forecastRes.ok) {
                const forecastData = await forecastRes.json();
                setStations(forecastData.stations);
            }

            if (spotsRes.ok && map.current) {
                const spotsData = await spotsRes.json();
                addFishingSpots(spotsData.features);
            }
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }, [selectedSpecies]);

    useEffect(() => {
        if (map.current || !mapContainer.current) return;

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
            fetchData();
        });

        return () => {
            map.current?.remove();
            map.current = null;
        };
    }, [fetchData]);

    useEffect(() => {
        if (map.current?.loaded()) {
            fetchData();
        }
    }, [selectedSpecies, fetchData]);

    useEffect(() => {
        if (!map.current || stations.length === 0) return;

        markersRef.current.forEach((marker) => marker.remove());
        markersRef.current = [];

        stations.forEach((station) => {
            const score = station.bite_scores[0]?.score || 50;
            const status = station.bite_scores[0]?.status || "Fair";

            const color =
                score >= 75 ? "#22c55e" : score >= 55 ? "#eab308" : score >= 35 ? "#f97316" : "#ef4444";

            const el = document.createElement("div");
            el.className = "station-marker";
            el.style.cssText = `
        width: 36px;
        height: 36px;
        background: radial-gradient(circle, ${color}dd 0%, ${color}44 70%, transparent 100%);
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 11px;
        color: white;
        text-shadow: 0 1px 2px rgba(0,0,0,0.8);
        box-shadow: 0 0 20px ${color}66;
        transition: transform 0.2s;
      `;
            el.textContent = score.toString();
            el.onmouseenter = () => (el.style.transform = "scale(1.2)");
            el.onmouseleave = () => (el.style.transform = "scale(1)");

            const popup = new maplibregl.Popup({ offset: 25, closeButton: false }).setHTML(`
        <div style="background: #1e293b; color: white; padding: 12px; border-radius: 8px; min-width: 180px;">
          <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">${station.station_name}</h3>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #94a3b8;">Score:</span>
            <span style="color: ${color}; font-weight: 600;">${score} (${status})</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #94a3b8;">Flow:</span>
            <span>${station.discharge?.toFixed(1) || "N/A"} m³/s</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: #94a3b8;">Temp:</span>
            <span>${station.weather.temperature}°C</span>
          </div>
        </div>
      `);

            const marker = new maplibregl.Marker({ element: el })
                .setLngLat([station.longitude, station.latitude])
                .setPopup(popup)
                .addTo(map.current!);

            el.onclick = () => onStationSelect(station);
            markersRef.current.push(marker);
        });

        if (map.current.getSource("heatmap")) {
            map.current.removeLayer("heatmap-layer");
            map.current.removeSource("heatmap");
        }

        const heatmapData = {
            type: "FeatureCollection" as const,
            features: stations.map((s) => ({
                type: "Feature" as const,
                properties: { weight: (s.bite_scores[0]?.score || 50) / 100 },
                geometry: { type: "Point" as const, coordinates: [s.longitude, s.latitude] },
            })),
        };

        map.current.addSource("heatmap", { type: "geojson", data: heatmapData });
        map.current.addLayer({
            id: "heatmap-layer",
            type: "heatmap",
            source: "heatmap",
            paint: {
                "heatmap-weight": ["get", "weight"],
                "heatmap-intensity": 1,
                "heatmap-radius": 50,
                "heatmap-opacity": 0.6,
                "heatmap-color": [
                    "interpolate",
                    ["linear"],
                    ["heatmap-density"],
                    0, "rgba(0,0,0,0)",
                    0.2, "#ef4444",
                    0.4, "#f97316",
                    0.6, "#eab308",
                    0.8, "#22c55e",
                    1, "#10b981",
                ],
            },
        });
    }, [stations, onStationSelect]);

    const addFishingSpots = (features: FishingSpot[]) => {
        if (!map.current) return;

        if (map.current.getSource("fishing-spots")) {
            map.current.removeLayer("fishing-spots-layer");
            map.current.removeSource("fishing-spots");
        }

        map.current.addSource("fishing-spots", {
            type: "geojson",
            data: { type: "FeatureCollection", features },
        });

        map.current.addLayer({
            id: "fishing-spots-layer",
            type: "circle",
            source: "fishing-spots",
            paint: {
                "circle-radius": 6,
                "circle-color": "#3b82f6",
                "circle-stroke-width": 2,
                "circle-stroke-color": "#1e40af",
                "circle-opacity": 0.8,
            },
        });
    };

    return (
        <div ref={mapContainer} className="w-full h-full" />
    );
}
