import { useEffect, useRef, useState } from 'react';
import {
  activateBiblePreset,
  deactivateBiblePreset,
  deleteBiblePreset,
  getBiblePresets,
  uploadBiblePreset,
} from '../../lib/api';
import type { BiblePreset } from '../../types/tax_credit';

interface BiblePresetSelectorProps {
  /** Called after any change that affects the bible (activate/deactivate/delete). */
  onBibleChanged: () => void;
  /** Increment this to force the preset list to reload (e.g. after creating a new preset). */
  refreshTrigger?: number;
}

export default function BiblePresetSelector({ onBibleChanged, refreshTrigger }: BiblePresetSelectorProps) {
  const [presets, setPresets] = useState<BiblePreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Upload state
  const [showUpload, setShowUpload] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Per-preset action state
  const [actionId, setActionId] = useState<number | null>(null);

  const load = async () => {
    try {
      const data = await getBiblePresets();
      setPresets(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load presets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [refreshTrigger]);

  const activePreset = presets.find((p) => p.is_active);

  const handleActivate = async (id: number) => {
    setActionId(id);
    setError(null);
    try {
      await activateBiblePreset(id);
      await load();
      onBibleChanged();
    } catch (e: any) {
      setError(e.message || 'Failed to activate preset');
    } finally {
      setActionId(null);
    }
  };

  const handleDeactivate = async (id: number) => {
    setActionId(id);
    setError(null);
    try {
      await deactivateBiblePreset(id);
      await load();
      onBibleChanged();
    } catch (e: any) {
      setError(e.message || 'Failed to deactivate preset');
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (preset: BiblePreset) => {
    if (!window.confirm(`Delete "${preset.name}"? This cannot be undone.`)) return;
    setActionId(preset.id);
    setError(null);
    try {
      await deleteBiblePreset(preset.id);
      await load();
      if (preset.is_active) onBibleChanged();
    } catch (e: any) {
      setError(e.message || 'Failed to delete preset');
    } finally {
      setActionId(null);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) { setUploadError('Please select a file'); return; }
    if (!uploadName.trim()) { setUploadError('Please enter a name'); return; }
    setUploading(true);
    setUploadError(null);
    try {
      await uploadBiblePreset(uploadFile, uploadName.trim());
      setShowUpload(false);
      setUploadName('');
      setUploadFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await load();
    } catch (e: any) {
      setUploadError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-3">
      {/* Header row */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <span className="text-sm font-semibold text-gray-700">Bible Presets</span>
          <span className="ml-2 text-xs text-gray-500">
            {activePreset
              ? <>Active: <span className="font-medium text-green-700">{activePreset.name}</span></>
              : 'Using hardcoded defaults'}
          </span>
        </div>
        <button
          onClick={() => { setShowUpload((v) => !v); setUploadError(null); }}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-white text-gray-700 transition-colors"
        >
          {showUpload ? 'Cancel' : '+ Upload New Bible'}
        </button>
      </div>

      {/* Upload form */}
      {showUpload && (
        <div className="p-3 bg-white border border-gray-200 rounded-lg space-y-2">
          <div className="flex gap-2 flex-wrap items-end">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500 font-medium">Name</label>
              <input
                type="text"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                placeholder="e.g. My Updated Bible 2024"
                className="w-52 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500 font-medium">Excel File (.xlsx)</label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                className="text-sm text-gray-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium rounded transition-colors"
            >
              {uploading ? 'Uploading…' : 'Upload'}
            </button>
          </div>
          {uploadError && (
            <p className="text-xs text-red-600">{uploadError}</p>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="text-xs text-red-600">{error}</p>
      )}

      {/* Presets list */}
      {loading ? (
        <p className="text-xs text-gray-400">Loading…</p>
      ) : presets.length === 0 ? (
        <p className="text-xs text-gray-400">No presets yet. Upload an Excel bible to create one.</p>
      ) : (
        <div className="space-y-1.5">
          {presets.map((p) => (
            <div
              key={p.id}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg border text-sm ${
                p.is_active
                  ? 'bg-green-50 border-green-200'
                  : 'bg-white border-gray-200'
              }`}
            >
              <div className="flex-1 min-w-0">
                <span className="font-medium text-gray-800 truncate">{p.name}</span>
                <span className="ml-2 text-xs text-gray-400">{p.entry_count} accounts</span>
                {p.is_active && (
                  <span className="ml-2 text-xs font-medium px-1.5 py-0.5 rounded bg-green-100 text-green-700">
                    Active
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {p.is_active ? (
                  <button
                    onClick={() => handleDeactivate(p.id)}
                    disabled={actionId === p.id}
                    className="text-xs text-orange-500 hover:text-orange-700 hover:underline disabled:opacity-50"
                  >
                    {actionId === p.id ? '…' : 'Deactivate'}
                  </button>
                ) : (
                  <button
                    onClick={() => handleActivate(p.id)}
                    disabled={actionId === p.id}
                    className="text-xs text-blue-600 hover:text-blue-800 hover:underline disabled:opacity-50"
                  >
                    {actionId === p.id ? '…' : 'Activate'}
                  </button>
                )}
                <button
                  onClick={() => handleDelete(p)}
                  disabled={actionId === p.id}
                  className="text-xs text-red-400 hover:text-red-600 hover:underline disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
