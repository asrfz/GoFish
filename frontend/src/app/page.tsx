"use client";

import { useState } from "react";
import { Camera, MapPin, Heart, Info } from "lucide-react";
import FishScanner from "@/components/FishScanner";
import FishingMap from "@/components/FishingMap";
import SafetyGuide from "@/components/SafetyGuide";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"scan" | "map" | "safety">("scan");
  const [scannedFish, setScannedFish] = useState<any>(null);

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-900 to-blue-800">
      {/* Header */}
      <header className="bg-black bg-opacity-50 backdrop-blur-sm sticky top-0 z-40 border-b border-blue-400">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart className="w-8 h-8 text-red-500 fill-red-500" />
            <h1 className="text-3xl font-bold text-white">GoFish</h1>
            <span className="text-sm text-blue-300">v2.0</span>
          </div>
          <p className="text-blue-200 text-sm">Fish scanning • Location finding • Safety guides</p>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-black bg-opacity-30 border-b border-blue-400">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab("scan")}
              className={`px-6 py-4 font-semibold flex items-center gap-2 transition ${
                activeTab === "scan"
                  ? "text-white border-b-2 border-orange-400"
                  : "text-blue-300 hover:text-white"
              }`}
            >
              <Camera className="w-5 h-5" />
              Fish Scanner
            </button>
            <button
              onClick={() => setActiveTab("map")}
              className={`px-6 py-4 font-semibold flex items-center gap-2 transition ${
                activeTab === "map"
                  ? "text-white border-b-2 border-orange-400"
                  : "text-blue-300 hover:text-white"
              }`}
            >
              <MapPin className="w-5 h-5" />
              Fishing Spots
            </button>
            <button
              onClick={() => setActiveTab("safety")}
              className={`px-6 py-4 font-semibold flex items-center gap-2 transition ${
                activeTab === "safety"
                  ? "text-white border-b-2 border-orange-400"
                  : "text-blue-300 hover:text-white"
              }`}
            >
              <Info className="w-5 h-5" />
              Safety & Recipes
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === "scan" && (
          <div>
            <FishScanner onFishScanned={setScannedFish} />
            {scannedFish && (
              <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Scan Results</h2>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Identified Species</h3>
                    <p className="text-4xl font-bold text-orange-600 mb-2">{scannedFish.species}</p>
                    <p className="text-gray-600">
                      Confidence: <span className="font-semibold">{(scannedFish.confidence * 100).toFixed(1)}%</span>
                    </p>
                    <p className="text-sm text-gray-500 mt-2">Method: {scannedFish.method}</p>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Additional Info</h3>
                    <ul className="space-y-2 text-gray-600 text-sm">
                      <li>• PyTorch Model: {scannedFish.pytorch_confidence ? `${(scannedFish.pytorch_confidence * 100).toFixed(1)}%` : "N/A"}</li>
                      <li>• Vector Search: {scannedFish.vector_confidence ? `${(scannedFish.vector_confidence * 100).toFixed(1)}%` : "N/A"}</li>
                      <li>• Scanned with hybrid AI classification</li>
                      <li>• Check recipes and safety info below</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "map" && <FishingMap />}

        {activeTab === "safety" && (
          <SafetyGuide species={scannedFish?.species} />
        )}
      </div>

      {/* Footer */}
      <footer className="bg-black bg-opacity-50 border-t border-blue-400 mt-16 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-blue-300 text-sm">
          <p>GoFish © 2026 - Your AI-Powered Fishing Assistant</p>
          <p className="mt-2">Fish Scanner • Spot Finder • Safety Guide • Community</p>
        </div>
      </footer>
    </main>
  );
}
