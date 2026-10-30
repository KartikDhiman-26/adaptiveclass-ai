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
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          bar: 'bg-emerald-500',
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        };
      case 'blue':
        return {
          bg: 'bg-blue-50 text-blue-700 border-blue-200',
          bar: 'bg-blue-500',
          icon: <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
        };
      case 'amber':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          bar: 'bg-amber-500',
          icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
        };
      case 'red':
      default:
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200',
          bar: 'bg-rose-500',
          icon: <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
        };
    }
  };

  const style = getBadgeStyle();

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden flex flex-col justify-between">
      {statusColor === 'red' && (
        <div className="absolute top-0 right-0 w-16 h-16 pointer-events-none overflow-hidden">
          <div className="bg-rose-500 text-[9px] uppercase tracking-wider text-white font-bold py-0.5 text-center transform rotate-45 translate-x-4 translate-y-2 shadow-sm">
            GAP
          </div>
        </div>
      )}

      <div>
        <div className="flex justify-between items-start mb-2">
          <h4 className="text-sm font-semibold text-slate-900">{name}</h4>
          <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium border ${style.bg}`}>
            {style.icon}
            <span>{statusLabel}</span>
          </span>
        </div>

        <div className="flex items-baseline space-x-2 my-2">
          <span className="text-2xl font-bold tracking-tight text-slate-900">{percentage}%</span>
          <span className="text-xs text-slate-500">class mastery</span>
        </div>
      </div>

      <div className="mt-3">
        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${style.bar}`}
            style={{ width: `${Math.min(Math.max(percentage, 5), 100)}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};
