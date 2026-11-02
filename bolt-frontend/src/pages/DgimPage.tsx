import { useState, useMemo, useCallback } from 'react';
import { Activity, Play, RotateCcw, TrendingUp } from 'lucide-react';
import { Panel, PanelHeader } from '@/components/Panel';
import {
  createDgim, dgimProcessStream, generateRandomStream, dgimApproxCount,
} from '@/data/dgim';
import type { DgimState } from '@/data/types';

export function DgimPage() {
  const [windowSize, setWindowSize] = useState(50);
  const [streamLength, setStreamLength] = useState(200);
  const [bitProbability, setBitProbability] = useState(0.4);
  const [state, setState] = useState<DgimState>(() => createDgim(50));
  const [streamData, setStreamData] = useState<{
    bits: (0 | 1)[];
    exactCounts: number[];
    approxCounts: number[];
    errors: number[];
  } | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  const runSimulation = useCallback(() => {
    const bits = generateRandomStream(streamLength, bitProbability);
    const result = dgimProcessStream(bits, windowSize);
    setStreamData({ bits: result.exactBits as (0 | 1)[], exactCounts: result.exactCounts, approxCounts: result.approxCounts, errors: result.errors });
    setState(result.state);
    setCurrentIndex(streamLength - 1);
  }, [streamLength, bitProbability, windowSize]);

  const stepForward = useCallback(() => {
    if (!streamData) {
      runSimulation();
      return;
    }
    const nextIndex = Math.min(currentIndex + 1, streamData.bits.length - 1);
    if (nextIndex === currentIndex) return;
    // Rebuild DGIM state up to nextIndex
    const bits = streamData.bits.slice(0, nextIndex + 1);
    const result = dgimProcessStream(bits, windowSize);
    setState(result.state);
    setCurrentIndex(nextIndex);
  }, [streamData, currentIndex, windowSize, runSimulation]);

  const reset = useCallback(() => {
    setState(createDgim(windowSize));
    setStreamData(null);
    setCurrentIndex(0);
  }, [windowSize]);

  const handleWindowChange = useCallback((size: number) => {
    setWindowSize(size);
    setState(createDgim(size));
    if (streamData) {
      const bits = streamData.bits.slice(0, currentIndex + 1);
      const result = dgimProcessStream(bits, size);
      setState(result.state);
    }
  }, [streamData, currentIndex]);

  const currentExact = streamData?.exactCounts[currentIndex] ?? 0;
  const currentApprox = useMemo(() => dgimApproxCount(state), [state]);
  const currentError = currentExact > 0 ? Math.abs(currentApprox - currentExact) / currentExact : 0;

  const maxBucketSize = state.buckets.length > 0 ? Math.max(...state.buckets.map((b) => b.size)) : 0;

  return (
    <div className="p-5 space-y-4 animate-fade-in">
      {/* Explanation */}
      <Panel>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-navy-50 flex items-center justify-center shrink-0">
            <Activity className="w-4 h-4 text-navy-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-navy-700">DGIM Streaming Analytics</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              The Datar-Gionis-Indyk-Motwani algorithm estimates the number of 1-bits in a sliding window
              using O(log²N) space. Each bucket represents a power-of-two number of 1s. The algorithm
              maintains at most 2 buckets per size, merging when a third appears. The last bucket
              contributes only half its size, bounding the error to at most 50%.
            </p>
          </div>
        </div>
      </Panel>

      {/* Controls */}
      <Panel>
        <PanelHeader title="Stream Configuration" subtitle="Generate a bit stream and control playback" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1.5">Window Size: {windowSize}</label>
            <input type="range" min={10} max={200} step={10} value={windowSize} onChange={(e) => handleWindowChange(Number(e.target.value))} className="w-full accent-teal-500" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1.5">Stream Length: {streamLength}</label>
            <input type="range" min={50} max={1000} step={50} value={streamLength} onChange={(e) => setStreamLength(Number(e.target.value))} className="w-full accent-teal-500" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1.5">1-bit Probability: {(bitProbability * 100).toFixed(0)}%</label>
            <input type="range" min={0.1} max={0.9} step={0.05} value={bitProbability} onChange={(e) => setBitProbability(Number(e.target.value))} className="w-full accent-teal-500" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={runSimulation}
            className="flex items-center gap-1.5 px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 transition-colors"
          >
            <Play className="w-4 h-4" />
            Run Full Simulation
          </button>
          <button
            onClick={stepForward}
            disabled={!streamData && streamLength === 0}
            className="flex items-center gap-1.5 px-3 py-2 bg-navy-600 text-white text-sm font-medium rounded-lg hover:bg-navy-700 transition-colors"
          >
            <TrendingUp className="w-4 h-4" />
            Step Forward
          </button>
          <button
            onClick={reset}
            className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-600 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
          {streamData && (
            <span className="text-xs text-slate-400 ml-2">
              Position: {currentIndex + 1} / {streamData.bits.length}
            </span>
          )}
        </div>
      </Panel>

      {/* Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel>
          <PanelHeader title="Count Comparison" subtitle="Approximate vs exact 1-count" />
          <div className="space-y-3">
            <Comparison label="Exact Count (in window)" value={currentExact} color="navy" />
            <Comparison label="DGIM Approximate" value={currentApprox} color="teal" />
            <Comparison label="Absolute Error" value={Math.abs(currentApprox - currentExact)} color={Math.abs(currentApprox - currentExact) > 0 ? 'amber' : 'green'} />
            <div className="pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Relative Error</span>
                <span className={`text-sm font-bold ${currentError > 0.3 ? 'text-red-600' : currentError > 0.1 ? 'text-amber-600' : 'text-emerald-600'}`}>
                  {(currentError * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </Panel>

        <Panel className="lg:col-span-2">
          <PanelHeader title="Bucket Structure" subtitle={`${state.buckets.length} buckets · largest covers ${maxBucketSize} bits`} />
          {state.buckets.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-400">No buckets. Run the simulation to populate.</div>
          ) : (
            <div className="space-y-2">
              <div className="flex flex-wrap gap-1.5">
                {state.buckets.map((b, i) => (
                  <div
                    key={i}
                    className="flex flex-col items-center px-2.5 py-1.5 rounded-lg border text-center transition-colors"
                    style={{
                      backgroundColor: `rgba(20, 184, 166, ${0.1 + (Math.log2(b.size) / Math.log2(maxBucketSize || 1)) * 0.3})`,
                      borderColor: 'rgba(20, 184, 166, 0.3)',
                    }}
                  >
                    <span className="text-xs font-bold text-teal-700">{b.size}</span>
                    <span className="text-[9px] text-slate-400 mt-0.5">t={b.timestamp}</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-3 pt-2 border-t border-slate-100 text-xs text-slate-500">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-teal-500/20 border border-teal-500/30" />
                  <span>Bucket size (power of 2)</span>
                </div>
                <span>·</span>
                <span>Color intensity = relative size</span>
              </div>
            </div>
          )}
        </Panel>
      </div>

      {/* Stream Visualization */}
      {streamData && (
        <Panel>
          <PanelHeader title="Bit Stream" subtitle={`Showing last ${Math.min(windowSize, streamData.bits.length)} bits (current window)`} />
          <div className="flex flex-wrap gap-0.5">
            {streamData.bits.slice(Math.max(0, currentIndex - windowSize + 1), currentIndex + 1).map((bit, i) => {
              const globalIdx = Math.max(0, currentIndex - windowSize + 1) + i;
              return (
                <div
                  key={globalIdx}
                  className={`w-5 h-5 rounded-sm text-[8px] flex items-center justify-center font-mono transition-colors ${
                    bit === 1 ? 'bg-teal-500 text-white' : 'bg-slate-100 text-slate-300'
                  } ${globalIdx === currentIndex ? 'ring-2 ring-navy-400' : ''}`}
                  title={`Position ${globalIdx + 1}: ${bit}`}
                >
                  {bit}
                </div>
              );
            })}
          </div>
          {currentIndex < streamData.bits.length - 1 && (
            <div className="mt-3">
              <input
                type="range"
                min={0}
                max={streamData.bits.length - 1}
                value={currentIndex}
                onChange={(e) => {
                  const idx = Number(e.target.value);
                  const bits = streamData.bits.slice(0, idx + 1);
                  const result = dgimProcessStream(bits, windowSize);
                  setState(result.state);
                  setCurrentIndex(idx);
                }}
                className="w-full accent-navy-500"
              />
              <p className="text-xs text-slate-400 mt-1">Drag to scrub through the stream</p>
            </div>
          )}
        </Panel>
      )}

      {/* Error over time */}
      {streamData && streamData.errors.length > 0 && (
        <Panel>
          <PanelHeader title="Error Rate Over Time" subtitle="Relative error of DGIM approximation across the stream" />
          <div className="relative h-[120px]">
            <svg viewBox="0 0 100 40" className="w-full" style={{ height: 120 }} preserveAspectRatio="none">
              <defs>
                <linearGradient id="errorGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <line x1="0" y1="20" x2="100" y2="20" stroke="#e2e8f0" strokeWidth={0.3} strokeDasharray="2 2" />
              <line x1="0" y1="10" x2="100" y2="10" stroke="#fee2e2" strokeWidth={0.3} strokeDasharray="2 2" />
              {(() => {
                const errors = streamData.errors;
                const maxErr = Math.max(...errors, 0.01);
                const points = errors.map((e, i) => ({
                  x: (i / (errors.length - 1)) * 100,
                  y: 40 - (e / maxErr) * 35,
                }));
                const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ');
                const areaD = `${pathD} L 100 40 L 0 40 Z`;
                return (
                  <>
                    <path d={areaD} fill="url(#errorGrad)" />
                    <path d={pathD} fill="none" stroke="#f59e0b" strokeWidth={0.8} vectorEffect="non-scaling-stroke" />
                  </>
                );
              })()}
            </svg>
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
            <span>Stream start</span>
            <span>Max error: {(Math.max(...streamData.errors) * 100).toFixed(1)}%</span>
            <span>Stream end</span>
          </div>
        </Panel>
      )}
    </div>
  );
}

function Comparison({ label, value, color }: { label: string; value: number; color: 'navy' | 'teal' | 'amber' | 'green' }) {
  const styles = {
    navy: 'bg-navy-50 border-navy-100 text-navy-700',
    teal: 'bg-teal-50 border-teal-200 text-teal-700',
    amber: 'bg-amber-50 border-amber-200 text-amber-700',
    green: 'bg-emerald-50 border-emerald-200 text-emerald-700',
  };
  return (
    <div className={`rounded-lg p-2.5 border ${styles[color]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs opacity-80">{label}</span>
        <span className="text-lg font-bold">{value}</span>
      </div>
    </div>
  );
}
