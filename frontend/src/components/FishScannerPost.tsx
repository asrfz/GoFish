"use client";

import { useRef, useState } from "react";
import Webcam from "react-webcam";
import { Camera, Upload, Loader, CheckCircle2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FishScannerPostProps {
  onScanComplete?: (data: any) => void;
}

export default function FishScannerPost({ onScanComplete }: FishScannerPostProps) {
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
      if (onScanComplete) {
        onScanComplete({
          type: "scan",
          data: {
            species: data.species,
            confidence: data.confidence,
            method: data.method,
          },
        });
      }
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
        if (onScanComplete) {
          onScanComplete({
            type: "scan",
            data: {
              species: data.species,
              confidence: data.confidence,
              method: data.method,
            },
          });
        }
      };
      reader.readAsDataURL(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white">
      {/* Post Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Camera className="w-5 h-5" />
          Fish Scanner
        </h2>
        <p className="text-xs text-gray-500 mt-1">Identify fish species with AI</p>
      </div>

      {/* Webcam/Upload Section */}
      <div className="relative bg-gray-50">
        {!result ? (
          <div className="p-4 space-y-4">
            <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
              <Webcam
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                className="w-full h-full object-cover"
                videoConstraints={{
                  facingMode: "environment",
                }}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={capturePhoto}
                disabled={loading}
                className="flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white font-semibold py-3 rounded-lg transition"
              >
                {loading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Camera className="w-5 h-5" />
                    Capture
                  </>
                )}
              </button>

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="flex items-center justify-center gap-2 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 font-semibold py-3 rounded-lg transition"
              >
                <Upload className="w-5 h-5" />
                Upload
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        ) : (
          <div className="p-4 space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-green-700 mb-3">
                <CheckCircle2 className="w-5 h-5" />
                <span className="font-semibold">Scan Complete!</span>
              </div>
              <div className="space-y-2">
                <div>
                  <span className="text-xs text-gray-600">Species:</span>
                  <p className="text-2xl font-bold text-gray-900">{result.species}</p>
                </div>
                <div>
                  <span className="text-xs text-gray-600">Confidence:</span>
                  <p className="text-lg font-semibold text-blue-600">
                    {(result.confidence * 100).toFixed(1)}%
                  </p>
                </div>
                {result.method && (
                  <div>
                    <span className="text-xs text-gray-600">Method:</span>
                    <p className="text-sm text-gray-700">{result.method}</p>
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={() => {
                setResult(null);
                setError(null);
              }}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-3 rounded-lg transition"
            >
              Scan Another Fish
            </button>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg m-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
