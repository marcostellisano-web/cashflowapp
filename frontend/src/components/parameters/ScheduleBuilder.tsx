import { Plus, Trash2 } from 'lucide-react';
import type { ShootingBlock, EpisodeDelivery } from '../../types/production';

const BLOCK_TYPES = ['Shoot', 'Doc Shoot', 'Recre Shoot'];

interface ScheduleBuilderProps {
  episodeCount: number;
  blocks: ShootingBlock[];
  onBlocksChange: (blocks: ShootingBlock[]) => void;
  deliveries: EpisodeDelivery[];
  onDeliveriesChange: (deliveries: EpisodeDelivery[]) => void;
}

export default function ScheduleBuilder({
  episodeCount,
  blocks,
  onBlocksChange,
  deliveries,
  onDeliveriesChange,
}: ScheduleBuilderProps) {
  const addBlock = () => {
    const nextNum = blocks.length + 1;
    onBlocksChange([
      ...blocks,
      {
        block_number: nextNum,
        block_type: 'Shoot',
        shoot_start: '',
        shoot_end: '',
      },
    ]);
  };

  const removeBlock = (idx: number) => {
    onBlocksChange(blocks.filter((_, i) => i !== idx));
  };

  const updateBlock = (idx: number, field: string, value: any) => {
    const updated = [...blocks];
    updated[idx] = { ...updated[idx], [field]: value };
    onBlocksChange(updated);
  };

  const initDeliveries = () => {
    const eps: EpisodeDelivery[] = [];
    for (let i = 1; i <= episodeCount; i++) {
      eps.push({ episode_number: i, delivery_date: '' });
    }
    onDeliveriesChange(eps);
  };

  const updateDelivery = (idx: number, field: string, value: string) => {
    const updated = [...deliveries];
    updated[idx] = { ...updated[idx], [field]: value };
    onDeliveriesChange(updated);
  };

  return (
    <div className="space-y-6">
      {/* Shooting Blocks */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-gray-900">Shooting Blocks</h3>
          <button
            type="button"
            onClick={addBlock}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            <Plus className="w-4 h-4" /> Add Block
          </button>
        </div>

        {blocks.length === 0 ? (
          <p className="text-sm text-gray-400 italic">
            No shooting blocks yet. Click "Add Block" to define your shoot
            schedule.
          </p>
        ) : (
          <div className="space-y-3">
            {blocks.map((block, idx) => (
              <div
                key={idx}
                className="grid grid-cols-[80px_120px_1fr_1fr_40px] gap-3 items-end"
              >
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Block
                  </label>
                  <div className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-gray-50 text-center">
                    {block.block_number}
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Type
                  </label>
                  <select
                    value={block.block_type || 'Shoot'}
                    onChange={(e) =>
                      updateBlock(idx, 'block_type', e.target.value)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {BLOCK_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Shoot Start
                  </label>
                  <input
                    type="date"
                    value={block.shoot_start}
                    onChange={(e) =>
                      updateBlock(idx, 'shoot_start', e.target.value)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Shoot End
                  </label>
                  <input
                    type="date"
                    value={block.shoot_end}
                    onChange={(e) =>
                      updateBlock(idx, 'shoot_end', e.target.value)
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => removeBlock(idx)}
                  className="p-2 text-red-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Episode Deliveries */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-gray-900">Episode Deliveries</h3>
          {deliveries.length === 0 && (
            <button
              type="button"
              onClick={initDeliveries}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              Generate {episodeCount} episodes
            </button>
          )}
        </div>

        {deliveries.length === 0 ? (
          <p className="text-sm text-gray-400 italic">
            Click "Generate" to create delivery rows for each episode.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs font-medium text-gray-500">
                  <th className="px-2 py-1">Episode</th>
                  <th className="px-2 py-1">Rough Cut</th>
                  <th className="px-2 py-1">Picture Lock</th>
                  <th className="px-2 py-1">Online</th>
                  <th className="px-2 py-1">Mix</th>
                  <th className="px-2 py-1">Delivery *</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.map((del_, idx) => (
                  <tr key={idx}>
                    <td className="px-2 py-1 font-medium text-gray-700">
                      Ep {del_.episode_number}
                    </td>
                    {(['rough_cut_date', 'picture_lock_date', 'online_date', 'mix_date', 'delivery_date'] as const).map(
                      (field) => (
                        <td key={field} className="px-2 py-1">
                          <input
                            type="date"
                            value={(del_[field] as string) || ''}
                            onChange={(e) =>
                              updateDelivery(idx, field, e.target.value)
                            }
                            className="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          />
                        </td>
                      ),
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
