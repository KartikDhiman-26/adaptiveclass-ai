import React, { useState, useMemo } from 'react';
import { SubjectSummary, SubjectTopic } from '../types';
import { ChevronRight } from 'lucide-react';

interface TopicMasteryHeatmapProps {
  subjects: SubjectSummary[];
  onSelectTopic?: (topic: SubjectTopic, subject: SubjectSummary) => void;
}

export const TopicMasteryHeatmap: React.FC<TopicMasteryHeatmapProps> = ({
  subjects,
  onSelectTopic
}) => {
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'critical' | 'attention' | 'strong'>('all');
  const [subjectFilter, setSubjectFilter] = useState<string>('all');

  // Flatten all topics across all curriculum subjects
  const allTopicsWithSubject = useMemo(() => {
    return subjects.flatMap((subj) =>
      subj.topics.map((top) => ({
        topic: top,
        subject: subj
      }))
    );
  }, [subjects]);

  const filteredItems = useMemo(() => {
    return allTopicsWithSubject.filter(({ topic, subject }) => {
      const matchSubject = subjectFilter === 'all' || subject.id === subjectFilter;
      let matchTier = true;
      if (selectedFilter === 'critical') matchTier = topic.mastery < 45;
      else if (selectedFilter === 'attention') matchTier = topic.mastery >= 45 && topic.mastery < 65;
      else if (selectedFilter === 'strong') matchTier = topic.mastery >= 75;

      return matchSubject && matchTier;
    });
  }, [allTopicsWithSubject, selectedFilter, subjectFilter]);

  const getHeatmapColor = (mastery: number) => {
    if (mastery < 40) return 'bg-[#261214] border-[#5C1D20] text-rose-300 hover:border-[#A31C1B]';
    if (mastery < 55) return 'bg-amber-950/40 border-amber-600/40 text-amber-300 hover:border-amber-500';
    if (mastery < 75) return 'bg-[#14231C] border-[#20372B] text-emerald-200 hover:border-emerald-500/50';
    return 'bg-[#0B1B14] border-[#20372B] text-emerald-300 hover:border-emerald-400';
  };

  const getBadgeColor = (mastery: number) => {
    if (mastery < 40) return 'bg-[#3B1517] text-rose-200 border-[#5C1D20]';
    if (mastery < 55) return 'bg-amber-950/80 text-amber-200 border-amber-700/60';
    if (mastery < 75) return 'bg-[#1B3326] text-emerald-200 border-[#20372B]';
    return 'bg-[#0E261B] text-emerald-300 border-[#20372B]';
  };

  return (
    <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 shadow-sm space-y-5">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#343434]">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#C12A29] font-semibold">
              Curricular Diagnostic Heatmap
            </span>
            <span className="text-[#898582]">•</span>
            <span className="text-xs text-[#B7B3B0]">{allTopicsWithSubject.length} Evaluated Computational Concepts</span>
          </div>
          <h3 className="text-base font-bold text-[#F5F2EF] tracking-tight mt-0.5">
            Topic-Level Mastery Heatmap & Concept Granularity
          </h3>
        </div>

        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Subject Filter */}
          <select
            value={subjectFilter}
            onChange={(e) => setSubjectFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-xl bg-[#171717] border border-[#343434] text-xs text-[#F5F2EF] focus:outline-none focus:ring-1 focus:ring-[#A31C1B]"
          >
            <option value="all">All Subjects</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code}: {s.name}
              </option>
            ))}
          </select>

          {/* Tier Filters */}
          <div className="flex items-center space-x-1 bg-[#171717] p-1 rounded-xl border border-[#343434]">
            {(['all', 'critical', 'attention', 'strong'] as const).map((tier) => (
              <button
                key={tier}
                onClick={() => setSelectedFilter(tier)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize transition-all ${
                  selectedFilter === tier
                    ? 'bg-[#A31C1B] text-white shadow-xs font-semibold'
                    : 'text-[#B7B3B0] hover:text-[#F5F2EF]'
                }`}
              >
                {tier === 'all' ? 'All Tiers' : tier === 'critical' ? 'Critical (<45%)' : tier === 'attention' ? 'Attention' : 'Strong (≥75%)'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
        {filteredItems.map(({ topic, subject }) => {
          return (
            <div
              key={`${subject.id}-${topic.id}`}
              onClick={() => { if (onSelectTopic) onSelectTopic(topic, subject); }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  if (onSelectTopic) onSelectTopic(topic, subject);
                }
              }}
              className={`p-3.5 rounded-xl border transition-all text-left group cursor-pointer flex flex-col justify-between h-32 ${getHeatmapColor(
                topic.mastery
              )}`}
              aria-label={`Topic ${topic.name} in ${subject.name}: mastery ${topic.mastery}%. Status: ${topic.status}.`}
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#B7B3B0] font-semibold truncate max-w-[130px]">
                    {subject.code}
                  </span>
                  <span
                    className={`text-[10px] font-mono uppercase font-bold px-1.5 py-0.5 rounded border ${getBadgeColor(
                      topic.mastery
                    )}`}
                  >
                    {topic.mastery}%
                  </span>
                </div>

                <h4 className="text-xs font-bold text-[#F5F2EF] group-hover:text-white transition-colors line-clamp-2">
                  {topic.name}
                </h4>
              </div>

              <div className="pt-2 border-t border-[#343434]/60 flex items-center justify-between text-[11px] text-[#B7B3B0]">
                <span className="capitalize text-[#898582] font-mono text-[10px]">
                  {topic.difficulty} level
                </span>
                <span className="flex items-center space-x-0.5 group-hover:text-[#F5F2EF] transition-colors">
                  <span>View Details</span>
                  <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend strip */}
      <div className="pt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-[#B7B3B0] font-mono">
        <div className="flex flex-wrap items-center gap-4 text-[11px]">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded bg-[#A31C1B] inline-block" />
            <span>Critical Gap (&lt;40%)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded bg-amber-500 inline-block" />
            <span>Needs Attention (40-54%)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded bg-emerald-600 inline-block" />
            <span>Moderate (55-74%)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded bg-emerald-400 inline-block" />
            <span>Strong Mastery (≥75%)</span>
          </div>
        </div>

        <span className="text-[#898582] text-[11px]">
          Click any concept card to drill into topic recommendations
        </span>
      </div>
    </div>
  );
};
