import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';

const FishScanner = () => {
  const webcamRef = useRef(null);
  const [scanResult, setScanResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Capture image from webcam
  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (!imageSrc) {
      setError('Failed to capture image from webcam');
      return;
    }
    return imageSrc;
  }, [webcamRef]);

  // Send image to backend API
  const handleScanCatch = async () => {
    setIsLoading(true);
    setError(null);
    setScanResult(null);

    try {
      const imageBase64 = capture();
      
      if (!imageBase64) {
        throw new Error('Could not capture image');
      }

      const response = await fetch('http://localhost:8000/api/scan-fish', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: imageBase64,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to scan fish');
      }

      const data = await response.json();
      setScanResult(data);
    } catch (err) {
      console.error('Error scanning fish:', err);
      setError(err.message || 'An error occurred while scanning the fish');
    } finally {
      setIsLoading(false);
    }
  };

  const videoConstraints = {
    width: 1280,
    height: 720,
    facingMode: 'environment', // Use back camera on mobile
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-gray-50">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Fish Scanner</h1>
          <p className="text-gray-600">Point your camera at a fish and scan to identify it</p>
        </div>

        {/* Webcam Feed */}
        <div className="relative w-full bg-black rounded-lg overflow-hidden shadow-lg">
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={videoConstraints}
            className="w-full h-auto"
          />
          
          {/* Overlay while loading */}
          {isLoading && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <div className="text-white text-xl font-semibold">Scanning fish...</div>
            </div>
          )}
        </div>

        {/* Scan Button */}
        <button
          onClick={handleScanCatch}
          disabled={isLoading}
          className={`w-full py-4 px-6 rounded-lg font-semibold text-white transition-all duration-200 ${
            isLoading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 shadow-md hover:shadow-lg'
          }`}
        >
          {isLoading ? 'Scanning...' : 'Scan Catch'}
        </button>

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            <p className="font-semibold">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {/* Scan Result */}
        {scanResult && (
          <div className="p-6 bg-white rounded-lg shadow-lg border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Identified Species</h2>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-gray-200">
                <span className="font-semibold text-gray-700">Species:</span>
                <span className="text-lg text-gray-900 font-semibold">{scanResult.species}</span>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-gray-200">
                <span className="font-semibold text-gray-700">Confidence:</span>
                <span className={`text-lg font-semibold ${
                  scanResult.confidence >= 0.8 
                    ? 'text-green-600' 
                    : scanResult.confidence >= 0.6 
                    ? 'text-yellow-600' 
                    : 'text-red-600'
                }`}>
                  {(scanResult.confidence * 100).toFixed(1)}%
                </span>
              </div>

              {/* Method badge */}
              <div className="flex items-center justify-between py-2 border-b border-gray-200">
                <span className="font-semibold text-gray-700">Method:</span>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  scanResult.method?.includes('hybrid') 
                    ? 'bg-purple-100 text-purple-800'
                    : scanResult.method === 'pytorch'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-orange-100 text-orange-800'
                }`}>
                  {scanResult.method === 'hybrid_agree' ? 'Hybrid (Models Agree) ✨' :
                   scanResult.method === 'hybrid_disagree' ? 'Hybrid (PyTorch Primary)' :
                   scanResult.method === 'pytorch' ? 'PyTorch CNN' :
                   scanResult.method === 'vector' ? 'Vector Search' :
                   scanResult.method || 'Unknown'}
                </span>
              </div>

              {/* Detailed confidence breakdown if available */}
              {(scanResult.pytorch_confidence !== null || scanResult.vector_confidence !== null) && (
                <div className="pt-2 space-y-2 border-t border-gray-200">
                  {scanResult.pytorch_confidence !== null && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">PyTorch Model:</span>
                      <span className="text-gray-800 font-medium">
                        {(scanResult.pytorch_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                  {scanResult.vector_confidence !== null && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Vector Search:</span>
                      <span className="text-gray-800 font-medium">
                        {(scanResult.vector_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Confidence bar visualization */}
              <div className="pt-2">
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      scanResult.confidence >= 0.8 
                        ? 'bg-green-500' 
                        : scanResult.confidence >= 0.6 
                        ? 'bg-yellow-500' 
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${scanResult.confidence * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Combined confidence score
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FishScanner;
