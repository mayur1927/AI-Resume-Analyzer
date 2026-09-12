"use client";

import React from "react";
import { Sliders, AlertCircle, Check } from "lucide-react";

interface TargetRangeSelectorProps {
  targetMin: number;
  targetMax: number;
  onMinChange: (val: number) => void;
  onMaxChange: (val: number) => void;
  disabled?: boolean;
}

const PRESETS = [
  { label: "Standard Match", min: 75, max: 80, desc: "Balanced keyword alignment" },
  { label: "Target Match", min: 80, max: 85, desc: "Recommended for competitive roles" },
  { label: "High Match", min: 85, max: 90, desc: "Extensive keyword alignment" },
  { label: "Aggressive", min: 90, max: 95, desc: "Maximum targeted alignment" },
];

export const TargetRangeSelector: React.FC<TargetRangeSelectorProps> = ({
  targetMin,
  targetMax,
  onMinChange,
  onMaxChange,
  disabled = false,
}) => {
  const span = targetMax - targetMin;
  const isInvalidRange = targetMin < 0 || targetMax > 100 || targetMin >= targetMax || (span < 5 && targetMax < 100) || (targetMin === 100 && targetMax === 100);

  const handleMinSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) return;
    onMinChange(val);
    if (targetMax - val < 5 && val <= 95) {
      onMaxChange(Math.min(100, val + 5));
    }
  };

  const handleMaxSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) return;
    onMaxChange(val);
    if (val - targetMin < 5 && val >= 5) {
      onMinChange(Math.max(0, val - 5));
    }
  };

  const handleMinNumberInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) {
      onMinChange(0);
      return;
    }
    const clamped = Math.max(0, Math.min(95, val));
    onMinChange(clamped);
  };

  const handleMaxNumberInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) {
      onMaxChange(5);
      return;
    }
    const clamped = Math.max(5, Math.min(100, val));
    onMaxChange(clamped);
  };

  return (
    <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-emerald-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Desired ATS Match Range
          </h3>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 text-xs font-bold font-mono">
          <span>{targetMin}%</span>
          <span className="text-slate-500">–</span>
          <span>{targetMax}%</span>
        </div>
      </div>

      {/* Preset Buttons */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {PRESETS.map((preset) => {
          const isSelected = targetMin === preset.min && targetMax === preset.max;
          return (
            <button
              key={preset.label}
              type="button"
              disabled={disabled}
              onClick={() => {
                onMinChange(preset.min);
                onMaxChange(preset.max);
              }}
              className={`px-2.5 py-2 rounded-lg text-left transition-all border ${
                isSelected
                  ? "bg-emerald-950/70 border-emerald-600 text-emerald-200 ring-1 ring-emerald-500/40"
                  : "bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
              } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-xs font-bold">{preset.label}</span>
                {isSelected && <Check className="w-3 h-3 text-emerald-400" />}
              </div>
              <p className="text-[10px] text-slate-500 font-mono">{preset.min}% – {preset.max}%</p>
            </button>
          );
        })}
      </div>

      {/* Dual Sliders and Synchronized Numeric Inputs */}
      <div className="space-y-4 pt-2">
        {/* Min Score Control */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <label htmlFor="target-min-slider" className="text-slate-400 font-medium">
              Minimum Target Threshold
            </label>
            <div className="flex items-center gap-1">
              <input
                type="number"
                min={0}
                max={95}
                value={targetMin}
                disabled={disabled}
                onChange={handleMinNumberInput}
                className="w-14 px-2 py-0.5 text-right font-mono font-bold text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-emerald-500"
              />
              <span className="text-slate-500 font-mono">%</span>
            </div>
          </div>
          <input
            id="target-min-slider"
            type="range"
            min={0}
            max={95}
            step={1}
            value={targetMin}
            disabled={disabled}
            onChange={handleMinSlider}
            className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer disabled:opacity-50"
          />
        </div>

        {/* Max Score Control */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <label htmlFor="target-max-slider" className="text-slate-400 font-medium">
              Maximum Target Threshold
            </label>
            <div className="flex items-center gap-1">
              <input
                type="number"
                min={5}
                max={100}
                value={targetMax}
                disabled={disabled}
                onChange={handleMaxNumberInput}
                className="w-14 px-2 py-0.5 text-right font-mono font-bold text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-emerald-500"
              />
              <span className="text-slate-500 font-mono">%</span>
            </div>
          </div>
          <input
            id="target-max-slider"
            type="range"
            min={5}
            max={100}
            step={1}
            value={targetMax}
            disabled={disabled}
            onChange={handleMaxSlider}
            className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer disabled:opacity-50"
          />
        </div>
      </div>

      {/* Validation / Helper Info */}
      {isInvalidRange ? (
        <div className="flex items-center gap-2 p-2.5 rounded-lg bg-rose-950/50 border border-rose-800/60 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>
            {targetMin >= targetMax
              ? "Minimum target must be less than maximum target."
              : "Target range span must be at least 5% (e.g. 80% – 85%, 0% – 5%, 95% – 100%)."}
          </span>
        </div>
      ) : (
        <p className="text-[11px] text-slate-500 leading-relaxed">
          The optimizer will run bounded non-fabricating iterations until the score enters the <strong className="text-slate-300">{targetMin}% – {targetMax}%</strong> window or reaches the maximum safe evidence-supported score.
        </p>
      )}
    </div>
  );
};