"use client";

import { useState, useEffect } from "react";
import { Brain, Fish, AlertCircle, ChefHat, Loader2, CheckCircle2, XCircle } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MoorchehBrainPostProps {
  species?: string; // Species from scanned fish
  onAnalysisComplete?: (data: any) => void;
}

interface BrainAdvice {
  species: string;
  edibility_label: string;
  safety_summary: string[];
  recipes: Array<{
    title: string;
    steps: string[];
    source_snippet: string;
  }>;
  community_alerts: string[];
  facts?: string[];
}

export default function MoorchehBrainPost({ species, onAnalysisComplete }: MoorchehBrainPostProps) {
  const [loading, setLoading] = useState(false);
  const [advice, setAdvice] = useState<BrainAdvice | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [inputSpecies, setInputSpecies] = useState(species || "");

  useEffect(() => {
    if (species) {
      setInputSpecies(species);
      // Small delay to ensure component is mounted
      const timer = setTimeout(() => {
        fetchBrainAdvice(species);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [species]);

  const fetchBrainAdvice = async (fishSpecies: string) => {
    if (!fishSpecies.trim()) {
      setError("Please enter a fish species");
      return;
    }

    setLoading(true);
    setError(null);
    setAdvice(null);

    try {
      // First verify backend is reachable
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
      } catch (healthError) {
        if (healthError instanceof Error && healthError.name === 'AbortError') {
          throw new Error(`Backend timeout at ${API_URL}. Make sure the backend server is running: python app.py`);
        }
        throw new Error(`Cannot connect to backend at ${API_URL}. Make sure the backend server is running on port 8000.`);
      }

      const controller2 = new AbortController();
      const timeoutId2 = setTimeout(() => controller2.abort(), 15000);
      const response = await fetch(`${API_URL}/api/brain/advise`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          species: fishSpecies,
        }),
        signal: controller2.signal
      });
      clearTimeout(timeoutId2);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error (${response.status}): ${errorText || response.statusText}`);
      }

      const data = await response.json();
      setAdvice(data);

      if (onAnalysisComplete) {
        onAnalysisComplete({
          type: "brain",
          data: {
            title: `Analysis: ${fishSpecies}`,
            description: `Safety: ${data.edibility_label}`,
            species: fishSpecies,
            advice: data,
          },
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch advice";
      // More detailed error messages
      if (errorMessage.includes("fetch")) {
        setError("Could not connect to backend. Make sure the server is running on port 8000.");
      } else {
        setError(errorMessage);
      }
      console.error("Brain advice error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchBrainAdvice(inputSpecies);
  };

  const getEdibilityColor = (label: string) => {
    const lower = label.toLowerCase();
    if (lower.includes("safe") || lower.includes("edible")) {
      return "text-green-600 bg-green-50 border-green-200";
    }
    if (lower.includes("caution") || lower.includes("limit")) {
      return "text-yellow-600 bg-yellow-50 border-yellow-200";
    }
    if (lower.includes("avoid") || lower.includes("toxic")) {
      return "text-red-600 bg-red-50 border-red-200";
    }
    return "text-gray-600 bg-gray-50 border-gray-200";
  };

  return (
    <div className="bg-white">
      {/* Post Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Moorcheh Brain - Fish Intelligence
        </h2>
        <p className="text-xs text-gray-500 mt-1">
          Get safety info, facts, and recipes for any fish species
        </p>
      </div>

      {/* Species Input */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Fish Species
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputSpecies}
                onChange={(e) => setInputSpecies(e.target.value)}
                placeholder="e.g., Bass, Walleye, Trout..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                disabled={loading || !inputSpecies.trim()}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white font-semibold rounded-lg transition text-sm"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Analyze"
                )}
              </button>
            </div>
            {species && (
              <p className="text-xs text-blue-600 mt-1">
                💡 Auto-analyzing scanned species: {species}
              </p>
            )}
          </div>
        </form>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="p-8 flex flex-col items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-3" />
          <p className="text-sm text-gray-600">Analyzing fish species...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 m-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700">
            <XCircle className="w-5 h-5" />
            <p className="text-sm font-semibold">Error</p>
          </div>
          <p className="text-xs text-red-600 mt-1">{error}</p>
        </div>
      )}

      {/* Advice Display */}
      {advice && !loading && (
        <div className="p-4 space-y-4">
          {/* Edibility Status */}
          <div className={`rounded-lg p-4 border ${getEdibilityColor(advice.edibility_label)}`}>
            <div className="flex items-center gap-2 mb-2">
              {advice.edibility_label.toLowerCase().includes("safe") ||
              advice.edibility_label.toLowerCase().includes("edible") ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : (
                <AlertCircle className="w-5 h-5" />
              )}
              <h3 className="font-semibold text-lg">{advice.species}</h3>
            </div>
            <p className="font-medium">{advice.edibility_label}</p>
          </div>

          {/* Safety Summary */}
          {advice.safety_summary && advice.safety_summary.length > 0 && (
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center gap-2 mb-3">
                <AlertCircle className="w-5 h-5 text-blue-600" />
                <h3 className="text-sm font-semibold text-blue-900">Safety Information</h3>
              </div>
              <ul className="space-y-2">
                {advice.safety_summary.map((item, idx) => (
                  <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recipes */}
          {advice.recipes && advice.recipes.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <ChefHat className="w-5 h-5 text-orange-600" />
                <h3 className="text-sm font-semibold text-gray-900">Recipes & Cooking Methods</h3>
              </div>
              {advice.recipes.map((recipe, idx) => (
                <div key={idx} className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                  <h4 className="font-semibold text-gray-900 mb-2">{recipe.title}</h4>
                  <ol className="space-y-1 ml-4">
                    {recipe.steps.map((step, stepIdx) => (
                      <li key={stepIdx} className="text-sm text-gray-700 list-decimal">
                        {step}
                      </li>
                    ))}
                  </ol>
                  {recipe.source_snippet && (
                    <p className="text-xs text-gray-500 mt-2 italic">
                      {recipe.source_snippet}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Community Alerts */}
          {advice.community_alerts && advice.community_alerts.length > 0 && (
            <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-5 h-5 text-yellow-600" />
                <h3 className="text-sm font-semibold text-yellow-900">Community Alerts</h3>
              </div>
              <ul className="space-y-1">
                {advice.community_alerts.map((alert, idx) => (
                  <li key={idx} className="text-sm text-yellow-800">• {alert}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!advice && !loading && !error && (
        <div className="p-8 text-center">
          <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500 mb-1">Ready to analyze</p>
          <p className="text-xs text-gray-400">
            Enter a fish species or scan a fish to get started
          </p>
        </div>
      )}
    </div>
  );
}
