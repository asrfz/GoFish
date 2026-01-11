"use client";

import { useState, useEffect } from "react";
import { Home, Camera, Brain, MapPin, Users, Plus } from "lucide-react";
import FishScannerPost from "@/components/FishScannerPost";
import BestSpotsPost from "@/components/BestSpotsPost";
import MoorchehBrainPost from "@/components/MoorchehBrainPost";
import ActiveUsersPost from "@/components/ActiveUsersPost";
import FeedItem from "@/components/FeedItem";
import CreatePost from "@/components/CreatePost";

type Tab = "feed" | "scan" | "brain" | "spots" | "users";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<Tab>("feed");
  const [feedItems, setFeedItems] = useState<any[]>([]);
  const [scannedSpecies, setScannedSpecies] = useState<string | null>(null);
  const [showCreatePost, setShowCreatePost] = useState(false);

  // Initialize feed with hardcoded posts and saved items
  useEffect(() => {
    const hardcodedPosts = [
      {
        id: Date.now() - 86400000, // 1 day ago
        type: "post",
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        data: {
          author: "FishingPro92",
          authorAvatar: "🎣",
          content: "Just caught my personal best bass at Lake Simcoe! 8.5 lbs and fighting strong. The bite was amazing this morning with the overcast weather. #GoFish #BassFishing #OntarioFishing",
          image: "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&h=600&fit=crop",
          likes: 156,
          comments: 23,
        },
      },
      {
        id: Date.now() - 43200000, // 12 hours ago
        type: "post",
        timestamp: new Date(Date.now() - 43200000).toISOString(),
        data: {
          author: "TroutMaster",
          authorAvatar: "🐟",
          content: "Spring trout season is heating up! Found this beautiful 22-inch rainbow using a fly rod. Nothing beats the early morning hatch. Tight lines everyone! 🎣",
          image: "https://images.unsplash.com/photo-1583212292454-1fe6229603b7?w=800&h=600&fit=crop",
          likes: 203,
          comments: 34,
        },
      },
      {
        id: Date.now() - 21600000, // 6 hours ago
        type: "post",
        timestamp: new Date(Date.now() - 21600000).toISOString(),
        data: {
          author: "WalleyeWizard",
          authorAvatar: "🎣",
          content: "Pro tip: Walleye are most active during low light conditions. Caught 5 keepers today just before sunset using jigs near structure. Always check your local regulations! #Walleye #FishingTips",
          image: "https://images.unsplash.com/photo-1598295893369-1918ffaf89a2?w=800&h=600&fit=crop",
          likes: 128,
          comments: 18,
        },
      },
    ];

    // Load saved items from localStorage
    const savedItems = localStorage.getItem("gofish_feed");
    const saved = savedItems ? JSON.parse(savedItems) : [];
    
    // Combine hardcoded posts with saved items, avoiding duplicates
    const allItems = [...hardcodedPosts, ...saved].filter((item, index, self) =>
      index === self.findIndex((t) => t.id === item.id)
    );
    
    // Sort by timestamp (newest first)
    allItems.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    setFeedItems(allItems);
    localStorage.setItem("gofish_feed", JSON.stringify(allItems.slice(0, 50)));
  }, []);

  const saveToFeed = (item: any) => {
    // If item already has an id, use it; otherwise create one
    const itemWithId = item.id ? item : { ...item, id: Date.now() };
    const itemWithTimestamp = item.timestamp ? itemWithId : { ...itemWithId, timestamp: new Date().toISOString() };
    
    const newFeed = [itemWithTimestamp, ...feedItems];
    // Remove duplicates and keep last 50 items
    const uniqueFeed = newFeed.filter((item, index, self) =>
      index === self.findIndex((t) => t.id === item.id)
    );
    const limitedFeed = uniqueFeed.slice(0, 50);
    
    setFeedItems(limitedFeed);
    localStorage.setItem("gofish_feed", JSON.stringify(limitedFeed));
    
    // If it's a scan, set the species for Brain
    if (itemWithTimestamp.type === "scan" && itemWithTimestamp.data?.species) {
      setScannedSpecies(itemWithTimestamp.data.species);
      // Auto-switch to brain tab after scan
      setTimeout(() => setActiveTab("brain"), 500);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Instagram-style Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-300">
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">🐟</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">GoFish</h1>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowCreatePost(true)}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
              title="Create Post"
            >
              <Plus className="w-6 h-6 text-gray-700" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto pb-20">
        {activeTab === "feed" && (
          <div className="max-w-lg mx-auto">
            {feedItems.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-500 text-sm mb-4">Your feed is empty</p>
                <p className="text-gray-400 text-xs">Scan a fish, find spots, or check analytics to get started!</p>
              </div>
            ) : (
              feedItems.map((item) => (
                <FeedItem key={item.id} item={item} />
              ))
            )}
          </div>
        )}

        {activeTab === "scan" && (
          <div className="max-w-lg mx-auto">
            <FishScannerPost onScanComplete={saveToFeed} />
          </div>
        )}

        {activeTab === "spots" && (
          <div className="max-w-lg mx-auto">
            <BestSpotsPost onSpotFound={saveToFeed} />
          </div>
        )}

        {activeTab === "brain" && (
          <div className="max-w-lg mx-auto">
            <MoorchehBrainPost species={scannedSpecies || undefined} onAnalysisComplete={saveToFeed} />
          </div>
        )}

        {activeTab === "users" && (
          <div className="max-w-lg mx-auto">
            <ActiveUsersPost />
          </div>
        )}
      </main>

      {/* Bottom Navigation Bar (Instagram-style) */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-300 z-50">
        <div className="max-w-lg mx-auto px-2 py-2 flex items-center justify-around">
          <button
            onClick={() => setActiveTab("feed")}
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition ${
              activeTab === "feed" ? "text-black" : "text-gray-400"
            }`}
          >
            <Home className={`w-5 h-5 ${activeTab === "feed" ? "fill-current" : ""}`} />
            <span className="text-xs font-medium">Feed</span>
          </button>

          <button
            onClick={() => setActiveTab("spots")}
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition ${
              activeTab === "spots" ? "text-black" : "text-gray-400"
            }`}
          >
            <MapPin className={`w-5 h-5 ${activeTab === "spots" ? "fill-current" : ""}`} />
            <span className="text-xs font-medium">Spots</span>
          </button>

          <button
            onClick={() => setActiveTab("scan")}
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition ${
              activeTab === "scan" ? "text-black" : "text-gray-400"
            }`}
          >
            <Camera className={`w-5 h-5 ${activeTab === "scan" ? "fill-current" : ""}`} />
            <span className="text-xs font-medium">Scan</span>
          </button>

          <button
            onClick={() => setActiveTab("brain")}
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition ${
              activeTab === "brain" ? "text-black" : "text-gray-400"
            }`}
          >
            <Brain className={`w-5 h-5 ${activeTab === "brain" ? "fill-current" : ""}`} />
            <span className="text-xs font-medium">Brain</span>
          </button>

          <button
            onClick={() => setActiveTab("users")}
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition ${
              activeTab === "users" ? "text-black" : "text-gray-400"
            }`}
          >
            <Users className={`w-5 h-5 ${activeTab === "users" ? "fill-current" : ""}`} />
            <span className="text-xs font-medium">Users</span>
          </button>
        </div>
      </nav>

      {/* Create Post Modal */}
      {showCreatePost && (
        <CreatePost
          onPostCreated={saveToFeed}
          onClose={() => setShowCreatePost(false)}
        />
      )}
    </div>
  );
}
