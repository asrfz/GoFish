"use client";

import { useEffect, useState } from "react";
import { Info, Loader, ChefHat } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SafetyGuideProps {
  species?: string;
}

export default function SafetyGuide({ species }: SafetyGuideProps) {
  const [selectedSpecies, setSelectedSpecies] = useState(species || "walleye");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [supportedSpecies, setSupportedSpecies] = useState<string[]>([]);

  // Fetch supported species
  useEffect(() => {
    const fetchSpecies = async () => {
      try {
        const response = await fetch(`${API_URL}/api/species`);
        const speciesData = await response.json();
        setSupportedSpecies(speciesData.species);
      } catch (err) {
        console.error("Failed to fetch species:", err);
      }
    };
    fetchSpecies();
  }, []);

  // Fetch safety info
  useEffect(() => {
    const fetchSafetyInfo = async () => {
      if (!selectedSpecies) return;

      try {
        setLoading(true);
        const response = await fetch(`${API_URL}/api/brain/advise`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            species: selectedSpecies,
            preferences: {
              avoid_high_mercury: false,
              pregnant: false,
              catch_and_release: false,
            },
          }),
        });

        if (response.ok) {
          const safetyData = await response.json();
          setData(safetyData);
        }
      } catch (err) {
        console.error("Failed to fetch safety info:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSafetyInfo();
  }, [selectedSpecies]);

  return (
    <div className="space-y-6">
      {/* Selection */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Info className="w-6 h-6 text-blue-600" />
          Fish Safety & Recipes
        </h2>
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Select Species:
            </label>
            <select
              value={selectedSpecies}
              onChange={(e) => setSelectedSpecies(e.target.value)}
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
        </div>
      </div>

      {loading && (
        <div className="text-center py-12">
          <Loader className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-2" />
          <p className="text-gray-600">Loading safety information...</p>
        </div>
      )}

      {data && !loading && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Safety Info */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-red-500 to-pink-600 p-4">
              <h3 className="text-white font-bold text-lg">Safety Information</h3>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                  {data.edibility_label || "Edible"}
                </span>
              </div>
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-800">Key Safety Points:</h4>
                {data.safety_summary && data.safety_summary.length > 0 ? (
                  <ul className="space-y-2">
                    {data.safety_summary.map((point: string, idx: number) => (
                      <li key={idx} className="flex gap-2 text-gray-700 text-sm">
                        <span className="text-green-600 font-bold">✓</span>
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="bg-blue-50 p-4 rounded text-gray-700 text-sm">
                    <p>
                      {selectedSpecies.charAt(0).toUpperCase() + selectedSpecies.slice(1)} can be prepared by grilling,
                      baking, or pan-frying.
                    </p>
                    <p className="mt-2">Check local fishing regulations before consumption.</p>
                    <p className="mt-2">Ensure proper storage and handling.</p>
                  </div>
                )}
              </div>

              {data.community_alerts && data.community_alerts.length > 0 && (
                <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-400 p-4">
                  <h4 className="font-semibold text-yellow-900 mb-2">Community Alerts:</h4>
                  <ul className="space-y-1">
                    {data.community_alerts.map((alert: string, idx: number) => (
                      <li key={idx} className="text-yellow-800 text-sm">
                        • {alert}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Recipes */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-orange-500 to-yellow-600 p-4">
              <h3 className="text-white font-bold text-lg flex items-center gap-2">
                <ChefHat className="w-5 h-5" />
                Recipes
              </h3>
            </div>
            <div className="p-6">
              {data.recipes && data.recipes.length > 0 ? (
                <div className="space-y-4">
                  {data.recipes.map((recipe: any, idx: number) => (
                    <div key={idx} className="border rounded-lg p-4 hover:bg-gray-50 transition">
                      <h4 className="font-semibold text-gray-900 mb-2">{recipe.title}</h4>
                      <ol className="list-decimal list-inside space-y-1">
                        {recipe.steps && recipe.steps.length > 0 ? (
                          recipe.steps.map((step: string, stepIdx: number) => (
                            <li key={stepIdx} className="text-gray-700 text-sm">
                              {step}
                            </li>
                          ))
                        ) : (
                          <li className="text-gray-600 text-sm">
                            Follow traditional preparation methods
                          </li>
                        )}
                      </ol>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-orange-50 p-4 rounded text-gray-700 text-sm">
                  <h4 className="font-semibold mb-2">Pan-Seared {selectedSpecies.charAt(0).toUpperCase() + selectedSpecies.slice(1)}</h4>
                  <ol className="list-decimal list-inside space-y-2">
                    <li>Clean and fillet the fish</li>
                    <li>Season with salt, pepper, and lemon</li>
                    <li>Heat pan with olive oil to medium-high heat</li>
                    <li>Cook for 4-5 minutes per side until golden</li>
                    <li>Serve with fresh vegetables</li>
                  </ol>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!data && !loading && (
        <div className="bg-gray-100 rounded-lg p-12 text-center">
          <Info className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-700 font-semibold">Select a fish species above</p>
          <p className="text-gray-600 text-sm">Get safety information and recipes</p>
        </div>
      )}
    </div>
  );
}
