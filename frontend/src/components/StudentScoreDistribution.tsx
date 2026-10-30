import React, { useState } from 'react';
import { StudentStatusDistribution } from '../types';
import { Award, CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react';

interface StudentScoreDistributionProps {
  distribution: StudentStatusDistribution;
  onFilterTier?: (tier: string) => void;
}

export const StudentScoreDistribution: React.FC<StudentScoreDistributionProps> = ({
  distribution,
  onFilterTier
}) => {
  const [activeTier, setActiveTier] = useState<string | null>(null);

  const total = distribution.total || 80;
  const advancedPct = Math.round((distribution.advanced / total) * 100);
  const onTrackPct = Math.round((distribution.on_track / total) * 100);
  const supportPct = Math.round((distribution.needs_support / total) * 100);
  const attentionPct = Math.round((distribution.needs_attention / total) * 100);

  const tiers = [
    {
      id: 'advanced',
      name: 'Advanced Learners',
      range: '≥85% Cumulative Mastery',
      count: distribution.advanced,
      percent: advancedPct,
      color: 'bg-emerald-400',
      textColor: 'text-emerald-400',
      bgColor: 'bg-[#0B1B14] border-[#20372B]',
      icon: Award,
      summary: 'Ready for independent algorithmic problem-solving and peer leadership.'
    },
    {
      id: 'on track',
      name: 'On Track',
      range: '55% – 84% Mastery',
      count: distribution.on_track,
      percent: onTrackPct,
      color: 'bg-emerald-600',
      textColor: 'text-emerald-300',
      bgColor: 'bg-[#14231C] border-[#20372B]',
      icon: CheckCircle2,
      summary: 'Solid foundational comprehension; progressing steadily through active practice.'
    },
    {
      id: 'needs support',
      name: 'Needs Support',
      range: '40% – 54% Mastery',
      count: distribution.needs_support,
      percent: supportPct,
      color: 'bg-amber-400',
      textColor: 'text-amber-400',
      bgColor: 'bg-amber-950/40 border-amber-600/40',
      icon: AlertTriangle,
      summary: 'Specific concept deficits identified; benefit from targeted micro-lessons.'
    },
    {
      id: 'needs attention',
      name: 'Needs Attention',
      range: '<40% Critical Deficit',
      count: distribution.needs_attention,
      percent: attentionPct,
      color: 'bg-[#A31C1B]',
      textColor: 'text-[#C12A29]',
      bgColor: 'bg-[#261214] border-[#5C1D20]',
      icon: AlertOctagon,
      summary: 'Immediate instructional intervention required to prevent course drop-off.'
    }
  ];

  const handleCardClick = (tierId: string) => {
    setActiveTier(activeTier === tierId ? null : tierId);
    if (onFilterTier) {
      onFilterTier(tierId);
    }
  };

  return (
    <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-[#343434]">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#C12A29] font-semibold">
              Cohort Stratification
            </span>
            <span className="text-[#898582]">•</span>
            <span className="text-xs text-[#B7B3B0]">Total Enrolled: {total} Students</span>
          </div>
          <h3 className="text-base font-bold text-[#F5F2EF] tracking-tight mt-0.5">
            Student Mastery Distribution & Tier Breakdown
          </h3>
        </div>

        <div className="text-xs text-[#B7B3B0] font-mono">
          4 Calibrated Achievement Tiers
        </div>
      </div>

      {/* Proportional Stacked Bar */}
      <div className="space-y-2">
        <div className="h-4 w-full bg-[#06110C] rounded-full overflow-hidden flex p-0.5 border border-[#343434]">
          <div
            style={{ width: `${advancedPct}%` }}
            className="h-full bg-emerald-400 rounded-l-full transition-all duration-500 hover:opacity-90"
            title={`Advanced: ${distribution.advanced} students (${advancedPct}%)`}
          />
          <div
            style={{ width: `${onTrackPct}%` }}
            className="h-full bg-emerald-600 transition-all duration-500 hover:opacity-90"
            title={`On Track: ${distribution.on_track} students (${onTrackPct}%)`}
          />
          <div
            style={{ width: `${supportPct}%` }}
            className="h-full bg-amber-400 transition-all duration-500 hover:opacity-90"
            title={`Needs Support: ${distribution.needs_support} students (${supportPct}%)`}
          />
          <div
            style={{ width: `${attentionPct}%` }}
            className="h-full bg-[#A31C1B] rounded-r-full transition-all duration-500 hover:opacity-90"
            title={`Needs Attention: ${distribution.needs_attention} students (${attentionPct}%)`}
          />
        </div>

        {/* Bar Legend */}
        <div className="flex flex-wrap items-center justify-between text-[11px] text-[#B7B3B0] font-mono px-1">
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded bg-emerald-400" />
            <span>Adv: {advancedPct}% ({distribution.advanced})</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded bg-emerald-600" />
            <span>On Track: {onTrackPct}% ({distribution.on_track})</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded bg-amber-400" />
            <span>Support: {supportPct}% ({distribution.needs_support})</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded bg-[#A31C1B]" />
            <span>Attention: {attentionPct}% ({distribution.needs_attention})</span>
          </span>
        </div>
      </div>

      {/* 4 Interactive Tier Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {tiers.map((t) => {
          const isSelected = activeTier === t.id;
          const Icon = t.icon;

          return (
            <div
              key={t.id}
              onClick={() => handleCardClick(t.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleCardClick(t.id);
                }
              }}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? `${t.bgColor} ring-1 ring-[#A31C1B]`
                  : 'bg-[#171717] hover:bg-[#0B1B14] border-[#343434] hover:border-[#20372B]'
              }`}
              aria-label={`${t.name}: ${t.count} students (${t.percent}%). Click to filter roster.`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[11px] font-mono uppercase tracking-wider font-semibold ${t.textColor}`}>
                    {t.range}
                  </span>
                  <Icon className={`w-4 h-4 ${t.textColor}`} />
                </div>

                <div className="flex items-baseline space-x-2 my-1">
                  <span className="text-2xl font-bold font-mono text-[#F5F2EF] tabular-nums">
                    {t.count}
                  </span>
                  <span className="text-xs text-[#B7B3B0] font-mono">
                    students ({t.percent}%)
                  </span>
                </div>

                <h4 className="text-xs font-semibold text-[#F5F2EF] mt-1">
                  {t.name}
                </h4>

                <p className="text-[11px] text-[#B7B3B0] mt-2 leading-relaxed">
                  {t.summary}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-[#343434] flex items-center justify-between text-[10px] font-mono text-[#898582]">
                <span>Filter in roster</span>
                <span className="text-[#C12A29]">→</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
