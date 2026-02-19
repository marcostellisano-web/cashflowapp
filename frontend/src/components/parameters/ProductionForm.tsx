import { useState } from 'react';
import type { ProductionParameters, ShootingBlock, EpisodeDelivery } from '../../types/production';
import ScheduleBuilder from './ScheduleBuilder';

interface ProductionFormProps {
  episodeCount?: number;
  initialParams?: ProductionParameters | null;
  onSubmit: (params: ProductionParameters) => void;
  onBack: () => void;
}

export default function ProductionForm({ episodeCount, initialParams, onSubmit, onBack }: ProductionFormProps) {
  const [title, setTitle] = useState(initialParams?.title ?? '');
  const [epCount, setEpCount] = useState(initialParams?.episode_count ?? episodeCount ?? 6);
  const [prepStart, setPrepStart] = useState(initialParams?.prep_start ?? '');
  const [ppStart, setPpStart] = useState(initialParams?.pp_start ?? '');
  const [ppEnd, setPpEnd] = useState(initialParams?.pp_end ?? '');
  const [editStart, setEditStart] = useState(initialParams?.edit_start ?? '');
  const [finalDelivery, setFinalDelivery] = useState(initialParams?.final_delivery_date ?? '');
  const [firstPayrollWeek, setFirstPayrollWeek] = useState(initialParams?.first_payroll_week ?? '');
  const [blocks, setBlocks] = useState<ShootingBlock[]>(initialParams?.shooting_blocks ?? []);
  const [deliveries, setDeliveries] = useState<EpisodeDelivery[]>(initialParams?.episode_deliveries ?? []);
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
      episode_count: epCount,
      prep_start: prepStart,
      pp_start: ppStart,
      pp_end: ppEnd,
      edit_start: editStart,
      shooting_blocks: blocks,
      episode_deliveries: deliveries,
      final_delivery_date: finalDelivery,
      first_payroll_week: firstPayrollWeek || undefined,
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
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
              Episode Count *
            </label>
            <input
              type="number"
              value={epCount}
              onChange={(e) => {
                const newCount = Number(e.target.value);
                setEpCount(newCount);
                if (deliveries.length === 0 || newCount === deliveries.length) return;
                if (newCount < deliveries.length) {
                  setDeliveries(deliveries.slice(0, newCount));
                } else {
                  const extras: EpisodeDelivery[] = [];
                  for (let i = deliveries.length + 1; i <= newCount; i++) {
                    extras.push({ episode_number: i, delivery_date: '' });
                  }
                  setDeliveries([...deliveries, ...extras]);
                }
              }}
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 pt-2 border-t border-gray-100">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              First Payroll Week
            </label>
            <input
              type="date"
              value={firstPayrollWeek}
              onChange={(e) => setFirstPayrollWeek(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="sm:col-span-2 lg:col-span-4 flex items-end">
            <p className="text-xs text-gray-400 pb-2">
              Payroll runs every 2 weeks from this date. Other payables fall on the
              alternating weeks.
            </p>
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
