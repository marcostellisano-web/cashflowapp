import { useState } from 'react';
import type { ProductionParameters, ShootingBlock, EpisodeDelivery } from '../../types/production';
import ScheduleBuilder from './ScheduleBuilder';

interface ProductionFormProps {
  episodeCount?: number;
  onSubmit: (params: ProductionParameters) => void;
  onBack: () => void;
}

export default function ProductionForm({ episodeCount, onSubmit, onBack }: ProductionFormProps) {
  const [title, setTitle] = useState('');
  const [seriesNumber, setSeriesNumber] = useState<number | undefined>();
  const [epCount, setEpCount] = useState(episodeCount || 6);
  const [prepStart, setPrepStart] = useState('');
  const [ppStart, setPpStart] = useState('');
  const [ppEnd, setPpEnd] = useState('');
  const [editStart, setEditStart] = useState('');
  const [finalDelivery, setFinalDelivery] = useState('');
  const [blocks, setBlocks] = useState<ShootingBlock[]>([]);
  const [deliveries, setDeliveries] = useState<EpisodeDelivery[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title || !prepStart || !ppStart || !ppEnd || !editStart || !finalDelivery) {
      setError('Please fill in all required fields.');
      return;
    }
    if (blocks.length === 0) {
      setError('Please add at least one shooting block.');
      return;
    }
    if (deliveries.length === 0) {
      setError('Please add episode delivery dates.');
      return;
    }

    onSubmit({
      title,
      series_number: seriesNumber,
      episode_count: epCount,
      prep_start: prepStart,
      pp_start: ppStart,
      pp_end: ppEnd,
      edit_start: editStart,
      shooting_blocks: blocks,
      episode_deliveries: deliveries,
      final_delivery_date: finalDelivery,
      hiatus_periods: [],
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Production Parameters</h2>
          <p className="text-sm text-gray-500">Enter the production schedule details.</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onBack}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
          >
            Back
          </button>
          <button
            type="submit"
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Next: Distribution
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Basic info */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
        <h3 className="font-medium text-gray-900">Production Info</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Production title"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Series Number
            </label>
            <input
              type="number"
              value={seriesNumber ?? ''}
              onChange={(e) =>
                setSeriesNumber(e.target.value ? Number(e.target.value) : undefined)
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., 1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Episode Count *
            </label>
            <input
              type="number"
              value={epCount}
              onChange={(e) => setEpCount(Number(e.target.value))}
              min={1}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Key dates */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
        <h3 className="font-medium text-gray-900">Key Dates</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prep Start *
            </label>
            <input
              type="date"
              value={prepStart}
              onChange={(e) => setPrepStart(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              PP Start *
            </label>
            <input
              type="date"
              value={ppStart}
              onChange={(e) => setPpStart(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              PP End *
            </label>
            <input
              type="date"
              value={ppEnd}
              onChange={(e) => setPpEnd(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Edit Start *
            </label>
            <input
              type="date"
              value={editStart}
              onChange={(e) => setEditStart(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Final Delivery *
            </label>
            <input
              type="date"
              value={finalDelivery}
              onChange={(e) => setFinalDelivery(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Schedule builder */}
      <ScheduleBuilder
        episodeCount={epCount}
        blocks={blocks}
        onBlocksChange={setBlocks}
        deliveries={deliveries}
        onDeliveriesChange={setDeliveries}
      />
    </form>
  );
}
