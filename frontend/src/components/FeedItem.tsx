"use client";

import { Heart, MessageCircle, Share2, Bookmark } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface FeedItemProps {
  item: {
    id: number;
    type: "scan" | "spot" | "brain" | "post";
    timestamp: string;
    data: any;
  };
}

export default function FeedItem({ item }: FeedItemProps) {
  const getTypeIcon = () => {
    if (item.type === "post") {
      return item.data.authorAvatar || "🎣";
    }
    switch (item.type) {
      case "scan":
        return "📸";
      case "spot":
        return "📍";
      case "brain":
        return "🧠";
      default:
        return "🐟";
    }
  };

  const getTypeLabel = () => {
    if (item.type === "post") {
      return item.data.author || "GoFish User";
    }
    switch (item.type) {
      case "scan":
        return "Fish Scan";
      case "spot":
        return "Fishing Spot Found";
      case "brain":
        return "Analytics Update";
      default:
        return "Activity";
    }
  };

  const renderContent = () => {
    if (item.type === "post") {
      return (
        <div>
          {item.data.image && (
            <img
              src={item.data.image}
              alt="Post"
              className="w-full h-auto object-cover"
              onError={(e) => {
                // Fallback if image fails to load
                e.currentTarget.style.display = 'none';
              }}
            />
          )}
          <div className="p-4">
            <p className="text-sm text-gray-900 whitespace-pre-wrap">{item.data.content}</p>
          </div>
        </div>
      );
    }

    if (item.type === "scan") {
      return (
        <div className="p-4">
          <div className="mb-3">
            <span className="text-2xl font-bold text-gray-900">{item.data.species}</span>
            <p className="text-sm text-gray-600 mt-1">
              Confidence: {(item.data.confidence * 100).toFixed(1)}%
            </p>
          </div>
          {item.data.method && (
            <p className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded inline-block">
              {item.data.method}
            </p>
          )}
        </div>
      );
    }

    if (item.type === "spot") {
      return (
        <div className="p-4">
          <div className="mb-3">
            <span className="text-xl font-bold text-gray-900">{item.data.name}</span>
            <p className="text-sm text-gray-600 mt-1">
              Bite Score: <span className="font-semibold">{item.data.bite_score}/100</span>
            </p>
            <p className="text-xs text-gray-500 mt-1">{item.data.reasoning}</p>
          </div>
        </div>
      );
    }

    if (item.type === "brain") {
      return (
        <div className="p-4">
          <div className="mb-3">
            <span className="text-xl font-bold text-gray-900">{item.data.title}</span>
            <p className="text-sm text-gray-600 mt-1">{item.data.description}</p>
          </div>
          {item.data.stats && (
            <div className="grid grid-cols-3 gap-2 mt-3">
              {item.data.stats.map((stat: any, idx: number) => (
                <div key={idx} className="bg-gray-50 rounded p-2 text-center">
                  <p className="text-xs text-gray-500">{stat.label}</p>
                  <p className="text-sm font-bold text-gray-900">{stat.value}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }
  };

  return (
    <article className="bg-white border-b border-gray-200">
      {/* Post Header */}
      <div className="px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white text-lg">
            {getTypeIcon()}
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">
              {item.type === "post" ? item.data.author || "GoFish" : "GoFish"}
            </p>
            <p className="text-xs text-gray-500">{getTypeLabel()}</p>
          </div>
        </div>
        <span className="text-xs text-gray-400">
          {item.timestamp
            ? formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })
            : "Just now"}
        </span>
      </div>

      {/* Post Content */}
      <div className={item.type === "post" && item.data.image ? "" : "bg-gray-50"}>{renderContent()}</div>

      {/* Post Actions */}
      <div className="px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 text-gray-700 hover:text-red-500 transition">
            <Heart className="w-6 h-6" />
            <span className="text-sm">{item.data.likes || (item.type === "post" ? item.data.likes || 0 : 24)}</span>
          </button>
          <button className="flex items-center gap-2 text-gray-700 hover:text-blue-500 transition">
            <MessageCircle className="w-6 h-6" />
            <span className="text-sm">{item.data.comments || (item.type === "post" ? item.data.comments || 0 : 8)}</span>
          </button>
          <button className="text-gray-700 hover:text-gray-900 transition">
            <Share2 className="w-6 h-6" />
          </button>
        </div>
        <button className="text-gray-700 hover:text-gray-900 transition">
          <Bookmark className="w-6 h-6" />
        </button>
      </div>
    </article>
  );
}
