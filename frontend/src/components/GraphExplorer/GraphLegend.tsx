import { LABEL_COLORS } from './constants';

interface GraphLegendProps {
  activeLabels?: string[];
}

export default function GraphLegend({ activeLabels }: GraphLegendProps) {
  const entries = activeLabels
    ? activeLabels.filter(l => l in LABEL_COLORS).map(l => [l, LABEL_COLORS[l]] as const)
    : Object.entries(LABEL_COLORS);

  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1">
      {entries.map(([label, color]) => (
        <div key={label} className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
          <span className="text-[10px] text-gray-500">{label}</span>
        </div>
      ))}
    </div>
  );
}
