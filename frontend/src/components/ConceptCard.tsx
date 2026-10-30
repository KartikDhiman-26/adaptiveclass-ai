import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, TrendingUp } from 'lucide-react';

interface ConceptCardProps {
  name: string;
  percentage: number;
  statusLabel: string;
  statusColor: string;
  studentCount?: number;
}

export const ConceptCard: React.FC<ConceptCardProps> = ({
  name,
  percentage,
  statusLabel,
  statusColor,
}) => {
  const getBadgeStyle = () => {
    switch (statusColor) {
      case 'green':
        return {
          badge: 'bg-emerald-50 text-emerald-800 border-emerald-200/80',
          bar: 'bg-emerald-600',
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700 flex-shrink-0" />,
          isCritical: false
        };
      case 'blue':
        return {
          badge: 'bg-blue-50 text-blue-800 border-blue-200/80',
          bar: 'bg-blue-600',
          icon: <TrendingUp className="w-3.5 h-3.5 text-blue-700 flex-shrink-0" />,
          isCritical: false
        };
      case 'amber':
        return {
          badge: 'bg-amber-50 text-amber-800 border-amber-200/80',
          bar: 'bg-amber-500',
          icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" />,
          isCritical: false
        };
      case 'red':
      default:
        return {
          badge: 'bg-red-50 text-red-800 border-red-200/80',
          bar: 'bg-red-600',
          icon: <AlertOctagon className="w-3.5 h-3.5 text-red-700 flex-shrink-0" />,
          isCritical: true
        };
    }
  };

  const style = getBadgeStyle();

  return (
    <div
      className={`bg-white rounded-xl border p-4 transition-all duration-150 flex flex-col justify-between ${
        style.isCritical
          ? 'border-red-200 shadow-sm bg-gradient-to-b from-red-50/20 to-white'
          : 'border-stone-200/90 shadow-sm hover:border-stone-300'
      }`}
    >
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <h4 className="text-sm font-semibold text-stone-900 tracking-tight">{name}</h4>
          <span
            className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium border ${style.badge}`}
          >
            {style.icon}
            <span>{statusLabel}</span>
          </span>
        </div>

        <div className="flex items-baseline space-x-2 my-1">
          <span className="text-2xl font-bold tracking-tight text-stone-900 tabular-nums">
            {percentage}%
          </span>
          <span className="text-xs text-stone-500 font-normal">class mastery</span>
        </div>
      </div>

      <div className="mt-4 pt-2">
        <div className="flex justify-between items-center text-[10px] text-stone-400 mb-1 font-mono">
          <span>0%</span>
          <span className="text-stone-500 font-medium">40% support bar</span>
          <span>100%</span>
        </div>
        <div
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${name} class mastery: ${percentage}%`}
          className="relative w-full bg-stone-100 rounded-full h-2 overflow-hidden"
        >
          {/* Reference line for 40% threshold */}
          <div
            className="absolute top-0 bottom-0 left-[40%] w-0.5 bg-stone-300 z-10"
            title="Academic Support Threshold (40%)"
          />
          <div
            className={`h-full rounded-full transition-all duration-500 ${style.bar}`}
            style={{ width: `${Math.min(Math.max(percentage, 3), 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};
