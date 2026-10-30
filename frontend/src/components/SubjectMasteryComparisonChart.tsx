import React, { useState } from 'react';
import { SubjectSummary } from '../types';
import { Database, ArrowUpRight } from 'lucide-react';

interface SubjectMasteryComparisonChartProps {
  subjects: SubjectSummary[];
  onSelectSubject?: (subjectId: string) => void;
  selectedSubjectId?: string;
}

export const SubjectMasteryComparisonChart: React.FC<SubjectMasteryComparisonChartProps> = ({
  subjects,
  onSelectSubject,
  selectedSubjectId
}) => {
  const [hoveredSubject, setHoveredSubject] = useState<SubjectSummary | null>(null);

  // Target proficiency benchmark (70% threshold)
  const BENCHMARK = 70;

  return (
    <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-5 border-b border-[#343434]">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#C12A29] font-semibold">
              Curriculum Comparison
            </span>
            <span className="text-[#898582]">•</span>
            <span className="text-xs text-[#B7B3B0]">Class-wide Subject Diagnostics</span>
          </div>
          <h3 className="text-base font-bold text-[#F5F2EF] tracking-tight mt-0.5">
            Subject Mastery vs. 70% Department Benchmark
          </h3>
        </div>

        <div className="flex items-center space-x-4 text-xs font-mono text-[#B7B3B0]">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded bg-[#A31C1B] inline-block" />
            <span>Mastery Score</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-amber-400/80 inline-block" />
            <span>70% Benchmark</span>
          </div>
        </div>
      </div>

      {/* Chart Bars */}
      <div className="space-y-4">
        {subjects.map((subj) => {
          const isSelected = selectedSubjectId === subj.id;
          const isHovered = hoveredSubject?.id === subj.id;

          const barColor = isSelected
            ? 'from-[#7F1717] to-[#A31C1B]'
            : subj.overallAverage >= 75
            ? 'from-[#0B1B14] to-emerald-500'
            : subj.overallAverage >= 60
            ? 'from-[#20372B] to-[#3B6651]'
            : 'from-amber-700 to-amber-500';

          return (
            <div
              key={subj.id}
              onClick={() => { if (onSelectSubject) onSelectSubject(subj.id); }}
              onMouseEnter={() => setHoveredSubject(subj)}
              onMouseLeave={() => setHoveredSubject(null)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer group ${
                isSelected
                  ? 'bg-[#261214] border-[#A31C1B]/60 shadow-xs'
                  : 'bg-[#171717] hover:bg-[#0B1B14] border-[#343434] hover:border-[#20372B]'
              }`}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  if (onSelectSubject) onSelectSubject(subj.id);
                }
              }}
              aria-label={`Subject ${subj.name}: average mastery ${subj.overallAverage}%. Click to view subject report.`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-[#202020] text-[#B7B3B0] border border-[#343434]">
                    {subj.code}
                  </span>
                  <span className="text-sm font-semibold text-[#F5F2EF] group-hover:text-white transition-colors">
                    {subj.name}
                  </span>
                  {subj.isLiveDb && (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[#0B1B14] text-emerald-300 border border-[#20372B]">
                      <Database className="w-2.5 h-2.5" />
                      <span>Live DB (PostgreSQL)</span>
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-3 text-xs">
                  <span className="text-[#898582] font-mono text-[11px]">
                    Bottleneck: <strong className="text-[#C12A29] font-medium">{subj.weakestTopic}</strong> ({subj.weakestMastery}%)
                  </span>
                  <span className="font-mono font-bold text-[#F5F2EF] text-sm tabular-nums">
                    {subj.overallAverage}%
                  </span>
                  <ArrowUpRight className="w-4 h-4 text-[#898582] group-hover:text-[#C12A29] transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </div>
              </div>

              {/* Progress Track */}
              <div className="relative w-full h-3 bg-[#06110C] rounded-full overflow-hidden border border-[#343434]">
                {/* 70% Benchmark Indicator Marker */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-amber-400/80 z-10"
                  style={{ left: `${BENCHMARK}%` }}
                  title="Department 70% Target Benchmark"
                />

                {/* Fill bar */}
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${barColor} transition-all duration-500`}
                  style={{ width: `${subj.overallAverage}%` }}
                />
              </div>

              {/* Interactive Hover Detail Tray */}
              {(isHovered || isSelected) && (
                <div className="mt-2.5 pt-2 border-t border-[#343434] flex flex-wrap items-center justify-between text-[11px] text-[#B7B3B0] animate-in fade-in duration-100">
                  <div className="flex items-center space-x-3">
                    <span>Enrolled: <strong className="text-[#F5F2EF]">{subj.studentCount} Students</strong></span>
                    <span>•</span>
                    <span>Top Concept: <strong className="text-emerald-300">{subj.strongestTopic}</strong> ({subj.strongestMastery}%)</span>
                  </div>
                  <span className="text-[#C12A29] font-medium flex items-center space-x-1">
                    <span>Click to open comprehensive {subj.code} report</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
