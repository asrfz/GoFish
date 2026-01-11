"use client";

import { useRef, useState } from "react";
import Webcam from "react-webcam";
import { Camera, Upload, Loader } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FishScannerProps {
  onFishScanned?: (fish: any) => void;
}

export default function FishScanner({ onFishScanned }: FishScannerProps) {
  const webcamRef = useRef<Webcam>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const capturePhoto = async () => {
    if (!webcamRef.current) return;

    try {
      setLoading(true);
      setError(null);
      const imageSrc = webcamRef.current.getScreenshot();

      if (!imageSrc) {
        throw new Error("Failed to capture image");
      }

      const response = await fetch(`${API_URL}/api/scan-fish`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          image_base64: imageSrc,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      onFishScanned?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setLoading(true);
      setError(null);

      const reader = new FileReader();
      reader.onload = async (event) => {
        const imageBase64 = event.target?.result as string;

        const response = await fetch(`${API_URL}/api/scan-fish`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            image_base64: imageBase64,
          }),
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        setResult(data);
        onFishScanned?.(data);
      };
      reader.readAsDataURL(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-2 gap-6">
        {/* Webcam Section */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-orange-500 to-red-600 p-4">
            <h2 className="text-white text-lg font-bold flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Live Camera
            </h2>
          </div>
          <div className="p-6">
            <Webcam
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              className="w-full rounded-lg border-2 border-orange-200"
            />
            <button
              onClick={capturePhoto}
              disabled={loading}
              className="w-full mt-4 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Camera className="w-5 h-5" />
                  Capture & Scan
                </>
              )}
            </button>
          </div>
        </div>

        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-blue-500 to-cyan-600 p-4">
            <h2 className="text-white text-lg font-bold flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Upload Photo
            </h2>
          </div>
          <div className="p-6">
            <div
              className="border-2 border-dashed border-blue-300 rounded-lg p-8 text-center cursor-pointer hover:bg-blue-50 transition"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="w-12 h-12 text-blue-400 mx-auto mb-2" />
              <p className="text-gray-700 font-semibold">Click to upload</p>
              <p className="text-gray-500 text-sm">or drag and drop</p>
              <p className="text-gray-400 text-xs mt-2">JPG, PNG, up to 10MB</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              className="w-full mt-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Select Image
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded">
          <p className="font-bold">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Result Display */}
      {result && !loading && (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-green-500 to-emerald-600 p-4">
            <h2 className="text-white text-lg font-bold">✓ Scan Complete</h2>
          </div>
          <div className="p-6">
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <p className="text-gray-600 text-sm mb-2">Species</p>
                <p className="text-3xl font-bold text-orange-600">{result.species}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600 text-sm mb-2">Confidence</p>
                <p className="text-3xl font-bold text-blue-600">
                  {(result.confidence * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-center">
                <p className="text-gray-600 text-sm mb-2">Method</p>
                <p className="text-lg font-semibold text-gray-700 capitalize">
                  {result.method.replace(/_/g, " ")}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
