"use client";

import { useEffect, useRef } from "react";
import { Users, MapPin } from "lucide-react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

interface User {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  activity: string;
  lastActive: string;
  avatar: string;
}

const HARDCODED_USERS: User[] = [
  {
    id: "1",
    name: "Mike Angler",
    latitude: 45.5017,
    longitude: -73.5673,
    activity: "Caught 3 Bass at Lake Ontario",
    lastActive: "5 min ago",
    avatar: "🎣",
  },
  {
    id: "2",
    name: "Sarah Fisher",
    latitude: 43.6532,
    longitude: -79.3832,
    activity: "Scanned a Walleye - 89% confidence",
    lastActive: "12 min ago",
    avatar: "🐟",
  },
  {
    id: "3",
    name: "Jake Reeler",
    latitude: 44.2312,
    longitude: -76.4860,
    activity: "Found great spot: Georgian Bay",
    lastActive: "18 min ago",
    avatar: "🎣",
  },
  {
    id: "4",
    name: "Emma Waters",
    latitude: 45.5152,
    longitude: -75.6950,
    activity: "Caught 2 Trout near Ottawa River",
    lastActive: "25 min ago",
    avatar: "🐠",
  },
  {
    id: "5",
    name: "Alex Cast",
    latitude: 46.5197,
    longitude: -84.3458,
    activity: "Scanning Pike - analyzing safety",
    lastActive: "1 hour ago",
    avatar: "🎣",
  },
];

export default function ActiveUsersPost() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
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
      if (!mapContainer.current) {
        setTimeout(() => initializeMap(), 100);
      }
      return;
    }

    try {
      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: "https://tiles.openfreemap.org/styles/dark",
        center: [-79.5, 45.0],
        zoom: 6,
        attributionControl: false,
      });

      map.current.addControl(new maplibregl.NavigationControl(), "top-right");
      map.current.addControl(
        new maplibregl.AttributionControl({ compact: true }),
        "bottom-right"
      );

      map.current.on("load", () => {
        addUserMarkers();
      });
    } catch (error) {
      console.error("Failed to initialize map:", error);
    }
  };

  const addUserMarkers = () => {
    if (!map.current) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    HARDCODED_USERS.forEach((user) => {
      const el = document.createElement("div");
      el.className = "user-marker";
      el.style.cssText = `
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        border: 3px solid white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s;
      `;
      el.textContent = user.avatar;
      el.onmouseenter = () => (el.style.transform = "scale(1.2)");
      el.onmouseleave = () => (el.style.transform = "scale(1)");

      const popup = new maplibregl.Popup({ offset: 25, closeButton: false }).setHTML(`
        <div style="background: #1e293b; color: white; padding: 12px; border-radius: 8px; min-width: 220px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 24px;">${user.avatar}</span>
            <h3 style="margin: 0; font-size: 14px; font-weight: 600;">${user.name}</h3>
          </div>
          <p style="margin: 0 0 8px 0; font-size: 12px; color: #94a3b8;">${user.activity}</p>
          <p style="margin: 0; font-size: 11px; color: #64748b;">Active ${user.lastActive}</p>
        </div>
      `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([user.longitude, user.latitude])
        .setPopup(popup)
        .addTo(map.current);

      markersRef.current.push(marker);
    });

    // Fit bounds to show all users
    if (HARDCODED_USERS.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      HARDCODED_USERS.forEach((user) => {
        bounds.extend([user.longitude, user.latitude]);
      });
      map.current.fitBounds(bounds, { padding: 80 });
    }
  };

  return (
    <div className="bg-white">
      {/* Post Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Users className="w-5 h-5" />
          Active Users
        </h2>
        <p className="text-xs text-gray-500 mt-1">
          {HARDCODED_USERS.length} anglers active right now
        </p>
      </div>

      {/* Map */}
      <div className="p-4 bg-gray-50">
        <div
          ref={mapContainer}
          className="w-full rounded-lg overflow-hidden border border-gray-300 bg-gray-200"
          style={{ height: "400px", minHeight: "400px" }}
        />
      </div>

      {/* User List */}
      <div className="p-4 space-y-3 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
          <MapPin className="w-4 h-4" />
          Recent Activity
        </h3>
        <div className="space-y-2">
          {HARDCODED_USERS.map((user) => (
            <div
              key={user.id}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-xl">
                {user.avatar}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {user.name}
                </p>
                <p className="text-xs text-gray-600 truncate">{user.activity}</p>
                <p className="text-xs text-gray-400 mt-0.5">{user.lastActive}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
