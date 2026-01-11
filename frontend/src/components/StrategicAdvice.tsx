"use client";

import { Gauge, Droplets, Thermometer, Wind, TrendingUp, TrendingDown, X } from "lucide-react";

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

interface StrategicAdviceProps {
    station: StationData | null;
    onClose: () => void;
}

export default function StrategicAdvice({ station, onClose }: StrategicAdviceProps) {
    if (!station) {
        return (
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-slate-900/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6 w-96">
                <div className="text-center">
                    <Gauge className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-white mb-2">Select a Station</h3>
                    <p className="text-sm text-slate-400">
                        Click on any station marker to view detailed conditions and strategic fishing advice.
                    </p>
                </div>
            </div>
        );
    }

    const score = station.bite_scores[0]?.score || 50;
    const status = station.bite_scores[0]?.status || "Fair";
    const reasoning = station.bite_scores[0]?.reasoning || "Average conditions";
    const species = station.bite_scores[0]?.species || "All";

    const getStatusColor = (s: string) => {
        switch (s) {
            case "Great": return "text-emerald-400";
            case "Good": return "text-yellow-400";
            case "Fair": return "text-orange-400";
            default: return "text-red-400";
        }
    };

    const getAdvice = (s: string, discharge: number | null) => {
        if (s === "Great") return "Prime conditions! Head out now for best results.";
        if (s === "Good") return "Solid conditions. Focus on structure and cover.";
        if (s === "Fair") return "Moderate activity expected. Try different presentations.";
        return "Tough bite. Consider live bait or finesse techniques.";
    };

    return (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-slate-900/95 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-5 w-[480px] shadow-2xl shadow-black/50">
            <button
                onClick={onClose}
                className="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
            >
                <X className="w-4 h-4" />
            </button>

            <div className="flex items-start gap-4 mb-4">
                <div className="relative">
                    <div
                        className={`w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold ${score >= 75 ? "bg-emerald-500/20 text-emerald-400" :
                                score >= 55 ? "bg-yellow-500/20 text-yellow-400" :
                                    score >= 35 ? "bg-orange-500/20 text-orange-400" :
                                        "bg-red-500/20 text-red-400"
                            }`}
                    >
                        {score}
                    </div>
                </div>
                <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-1">{station.station_name}</h3>
                    <div className="flex items-center gap-2">
                        <span className={`font-medium ${getStatusColor(status)}`}>{status}</span>
                        <span className="text-slate-500">•</span>
                        <span className="text-slate-400 capitalize">{species}</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-4 gap-3 mb-4">
                <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                    <Droplets className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                    <p className="text-lg font-semibold text-white">
                        {station.discharge?.toFixed(1) || "—"}
                    </p>
                    <p className="text-xs text-slate-500">m³/s</p>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                    <Thermometer className="w-5 h-5 text-orange-400 mx-auto mb-1" />
                    <p className="text-lg font-semibold text-white">{station.weather.temperature}°</p>
                    <p className="text-xs text-slate-500">Celsius</p>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                    {station.weather.is_pressure_falling ? (
                        <TrendingDown className="w-5 h-5 text-purple-400 mx-auto mb-1" />
                    ) : (
                        <TrendingUp className="w-5 h-5 text-cyan-400 mx-auto mb-1" />
                    )}
                    <p className="text-lg font-semibold text-white">{station.weather.pressure.toFixed(0)}</p>
                    <p className="text-xs text-slate-500">hPa</p>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                    <Wind className="w-5 h-5 text-teal-400 mx-auto mb-1" />
                    <p className="text-lg font-semibold text-white">{station.weather.wind_speed.toFixed(0)}</p>
                    <p className="text-xs text-slate-500">km/h</p>
                </div>
            </div>

            <div className="bg-gradient-to-r from-emerald-900/30 to-cyan-900/30 rounded-xl p-4 border border-emerald-500/20">
                <h4 className="text-sm font-semibold text-emerald-400 mb-2">Strategic Advice</h4>
                <p className="text-sm text-slate-300">{getAdvice(status, station.discharge)}</p>
                <p className="text-xs text-slate-500 mt-2">Factors: {reasoning}</p>
            </div>
        </div>
    );
}
