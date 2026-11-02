import { useState, useCallback, useMemo } from 'react';
import { Filter, Plus, Search, Trash2, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { Panel, PanelHeader } from '@/components/Panel';
import {
  createBloomFilter, bloomInsert, bloomCheck, bloomExactCheck,
  bloomClear, evaluateFalsePositives, calcFalsePositiveRate,
} from '@/data/bloomFilter';
import type { BloomFilterState } from '@/data/types';

export function BloomFilterPage() {
  const [filterSize, setFilterSize] = useState(64);
  const [expectedItems, setExpectedItems] = useState(20);
  const [state, setState] = useState<BloomFilterState>(() => createBloomFilter(64, 20));
  const [insertValue, setInsertValue] = useState('');
  const [checkValue, setCheckValue] = useState('');
  const [checkResult, setCheckResult] = useState<{ item: string; bloom: boolean; exact: boolean } | null>(null);

  const rebuild = useCallback((size: number, expected: number) => {
    const newFilter = createBloomFilter(size, expected);
    for (const item of state.insertedItems) {
      const reinserted = bloomInsert(newFilter, item);
      newFilter.bitArray = reinserted.bitArray;
      newFilter.insertedItems = reinserted.insertedItems;
      newFilter.falsePositiveRate = reinserted.falsePositiveRate;
    }
    setState(newFilter);
  }, [state.insertedItems]);

  const handleInsert = useCallback(() => {
    const val = insertValue.trim();
    if (!val) return;
    setState((prev) => bloomInsert(prev, val));
    setInsertValue('');
  }, [insertValue]);

  const handleCheck = useCallback(() => {
    const val = checkValue.trim();
    if (!val) return;
    const bloom = bloomCheck(state, val);
    const exact = bloomExactCheck(state, val);
    setCheckResult({ item: val, bloom, exact });
  }, [state, checkValue]);

  const handleClear = useCallback(() => {
    setState((prev) => bloomClear(prev));
    setCheckResult(null);
  }, []);

  const handleSizeChange = useCallback((size: number) => {
    setFilterSize(size);
    rebuild(size, expectedItems);
  }, [expectedItems, rebuild]);

  const handleExpectedChange = useCallback((expected: number) => {
    setExpectedItems(expected);
    rebuild(filterSize, expected);
  }, [filterSize, rebuild]);

  const theoreticalFp = useMemo(() => calcFalsePositiveRate(state.insertedItems.length, state.size, state.hashCount), [state]);

  const testItems = useMemo(() => {
    const knownFalse = ['test-xyz', 'not-inserted', 'random-99', 'fake-item', 'nope-42', 'absent-7', 'missing-3', 'phantom-1'];
    return [...knownFalse, ...state.insertedItems];
  }, [state.insertedItems]);

  const evaluation = useMemo(() => evaluateFalsePositives(state, testItems), [state, testItems]);

  const setBits = state.bitArray.filter(Boolean).length;
  const utilization = (setBits / state.size) * 100;

  return (
    <div className="p-5 space-y-4 animate-fade-in">
      {/* Explanation */}
      <Panel>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-navy-50 flex items-center justify-center shrink-0">
            <Filter className="w-4 h-4 text-navy-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-navy-700">Bloom Filter Laboratory</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              A probabilistic data structure that tests set membership in O(k) time using k hash functions.
              It may produce false positives but never false negatives. Adjust the bit-array size and hash count
              to observe the trade-off between memory and accuracy.
            </p>
          </div>
        </div>
      </Panel>

      {/* Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel>
          <PanelHeader title="Configuration" subtitle="Filter parameters" />
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-500 block mb-1.5">Bit Array Size: {filterSize}</label>
              <input type="range" min={16} max={256} step={16} value={filterSize} onChange={(e) => handleSizeChange(Number(e.target.value))} className="w-full accent-teal-500" />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 block mb-1.5">Expected Items: {expectedItems}</label>
              <input type="range" min={5} max={100} step={5} value={expectedItems} onChange={(e) => handleExpectedChange(Number(e.target.value))} className="w-full accent-teal-500" />
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
              <Metric label="Hash Functions" value={String(state.hashCount)} />
              <Metric label="Items Inserted" value={String(state.insertedItems.length)} />
              <Metric label="Bits Set" value={`${setBits} / ${state.size}`} />
              <Metric label="Utilization" value={`${utilization.toFixed(0)}%`} />
            </div>
          </div>
        </Panel>

        {/* Insert + Check */}
        <Panel className="lg:col-span-2">
          <PanelHeader title="Operations" subtitle="Insert items and test membership" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Insert */}
            <div>
              <label className="text-xs font-medium text-slate-500 block mb-1.5">Insert Item</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={insertValue}
                  onChange={(e) => setInsertValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleInsert()}
                  placeholder="Enter a string to insert…"
                  className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400/30 focus:border-teal-400"
                />
                <button
                  onClick={handleInsert}
                  className="flex items-center gap-1 px-3 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Insert
                </button>
              </div>

              <div className="mt-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-slate-500">Inserted Items ({state.insertedItems.length})</span>
                  <button onClick={handleClear} className="flex items-center gap-1 text-xs text-red-500 hover:text-red-600 transition-colors">
                    <Trash2 className="w-3 h-3" /> Clear All
                  </button>
                </div>
                <div className="max-h-[120px] overflow-y-auto scrollbar-thin border border-slate-100 rounded-lg p-2 space-y-1">
                  {state.insertedItems.length === 0 ? (
                    <p className="text-xs text-slate-400 text-center py-4">No items inserted yet.</p>
                  ) : (
                    state.insertedItems.map((item, i) => (
                      <div key={i} className="flex items-center justify-between text-xs bg-slate-50 rounded px-2 py-1">
                        <span className="text-slate-700 truncate">{item}</span>
                        <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Check */}
            <div>
              <label className="text-xs font-medium text-slate-500 block mb-1.5">Check Membership</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={checkValue}
                  onChange={(e) => setCheckValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
                  placeholder="Enter a string to test…"
                  className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400/30 focus:border-teal-400"
                />
                <button
                  onClick={handleCheck}
                  className="flex items-center gap-1 px-3 py-2 bg-navy-600 text-white text-sm font-medium rounded-lg hover:bg-navy-700 transition-colors"
                >
                  <Search className="w-4 h-4" />
                  Check
                </button>
              </div>

              {checkResult && (
                <div className="mt-3 p-3 rounded-lg border animate-fade-in">
                  {checkResult.bloom ? (
                    checkResult.exact ? (
                      <div className="flex items-center gap-2 text-emerald-600">
                        <CheckCircle2 className="w-4 h-4" />
                        <div>
                          <p className="text-sm font-medium">"{checkResult.item}" is in the set</p>
                          <p className="text-xs text-emerald-500/70">Confirmed true positive</p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-amber-600">
                        <AlertCircle className="w-4 h-4" />
                        <div>
                          <p className="text-sm font-medium">"{checkResult.item}" may be in the set</p>
                          <p className="text-xs text-amber-500/70">False positive — item was never inserted</p>
                        </div>
                      </div>
                    )
                  ) : (
                    <div className="flex items-center gap-2 text-slate-500">
                      <XCircle className="w-4 h-4" />
                      <div>
                        <p className="text-sm font-medium">"{checkResult.item}" is NOT in the set</p>
                        <p className="text-xs text-slate-400">Definitely absent (true negative)</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </Panel>
      </div>

      {/* Bit Array Visualization */}
      <Panel>
        <PanelHeader title="Bit Array Visualization" subtitle={`${setBits} of ${state.size} bits set (${utilization.toFixed(0)}% utilized)`} />
        <div className="flex flex-wrap gap-1">
          {state.bitArray.map((bit, i) => (
            <div
              key={i}
              className={`w-5 h-5 rounded-sm text-[8px] flex items-center justify-center font-mono transition-colors ${
                bit ? 'bg-teal-500 text-white' : 'bg-slate-100 text-slate-300'
              }`}
              title={`Bit ${i}: ${bit ? '1' : '0'}`}
            >
              {bit ? '1' : '0'}
            </div>
          ))}
        </div>
      </Panel>

      {/* False Positive Evaluation */}
      <Panel>
        <PanelHeader title="False Positive Evaluation" subtitle="Theoretical vs empirical false positive rate" />
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          <Metric label="Theoretical FP Rate" value={`${(theoreticalFp * 100).toFixed(2)}%`} />
          <Metric label="Empirical FP Rate" value={`${(evaluation.rate * 100).toFixed(2)}%`} />
          <Metric label="True Positives" value={String(evaluation.truePositives)} />
          <Metric label="False Positives" value={String(evaluation.falsePositives)} accent={evaluation.falsePositives > 0 ? 'amber' : 'green'} />
          <Metric label="True Negatives" value={String(evaluation.trueNegatives)} />
        </div>
        <div className="bg-slate-50 rounded-lg p-3 text-xs text-slate-600">
          <p>
            Tested against {evaluation.total} items ({state.insertedItems.length} inserted + {evaluation.total - state.insertedItems.length} non-inserted).
            The Bloom filter reported {evaluation.falsePositives} false positive{evaluation.falsePositives !== 1 ? 's' : ''} out of {evaluation.trueNegatives + evaluation.falsePositives} truly absent items,
            yielding an empirical false positive rate of <span className="font-semibold text-navy-700">{(evaluation.rate * 100).toFixed(2)}%</span> versus the theoretical
            <span className="font-semibold text-navy-700"> {(theoreticalFp * 100).toFixed(2)}%</span>.
          </p>
        </div>
      </Panel>
    </div>
  );
}

function Metric({ label, value, accent }: { label: string; value: string; accent?: 'amber' | 'green' }) {
  const color = accent === 'amber' ? 'text-amber-600' : accent === 'green' ? 'text-emerald-600' : 'text-navy-700';
  return (
    <div className="bg-slate-50 rounded-lg p-2.5 border border-slate-100">
      <p className={`text-base font-bold leading-tight ${color}`}>{value}</p>
      <p className="text-[10px] text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}
