"use client";

import { Fish, Waves, Droplets } from "lucide-react";

interface SidebarProps {
    selectedSpecies: string;
    onSpeciesChange: (species: string) => void;
}

const speciesData = [
    { id: "walleye", name: "Walleye", icon: Fish, color: "#f59e0b" },
    { id: "bass", name: "Bass", icon: Waves, color: "#22c55e" },
    { id: "trout", name: "Trout", icon: Droplets, color: "#3b82f6" },
];

export default function Sidebar({ selectedSpecies, onSpeciesChange }: SidebarProps) {
    return (
        <div className="w-64 bg-slate-900/95 backdrop-blur-xl border-r border-slate-700/50 flex flex-col">
            <div className="p-6 border-b border-slate-700/50">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-xl">
                        <Fish className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">Ontario Angler</h1>
                        <p className="text-xs text-slate-400">Pro Edition</p>
                    </div>
                </div>
            </div>

            <div className="p-4">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                    Target Species
                </h2>
                <div className="space-y-2">
                    <button
                        onClick={() => onSpeciesChange("")}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${selectedSpecies === ""
                                ? "bg-gradient-to-r from-purple-600/30 to-pink-600/30 border border-purple-500/50 text-white"
                                : "bg-slate-800/50 text-slate-300 hover:bg-slate-700/50 border border-transparent"
                            }`}
                    >
                        <div className="p-1.5 bg-purple-500/20 rounded-lg">
                            <Fish className="w-4 h-4 text-purple-400" />
                        </div>
                        <span className="font-medium">All Species</span>
                    </button>

                    {speciesData.map((species) => {
                        const Icon = species.icon;
                        return (
                            <button
                                key={species.id}
                                onClick={() => onSpeciesChange(species.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${selectedSpecies === species.id
                                        ? "bg-gradient-to-r from-emerald-600/30 to-cyan-600/30 border border-emerald-500/50 text-white shadow-lg shadow-emerald-500/10"
                                        : "bg-slate-800/50 text-slate-300 hover:bg-slate-700/50 border border-transparent"
                                    }`}
                            >
                                <div
                                    className="p-1.5 rounded-lg"
                                    style={{ backgroundColor: `${species.color}20` }}
                                >
                                    <Icon className="w-4 h-4" style={{ color: species.color }} />
                                </div>
                                <span className="font-medium">{species.name}</span>
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className="mt-auto p-4 border-t border-slate-700/50">
                <div className="text-center">
                    <p className="text-xs text-slate-500">
                        Data: Environment Canada & Open-Meteo
                    </p>
                    <p className="text-xs text-slate-600 mt-1">No API keys required</p>
                </div>
            </div>
        </div>
    );
}
