import React, { useState, useMemo } from 'react';
import { SubjectSummary } from '../types';
import { 
  Search, ArrowRight, Database, 
  Layers, ChevronLeft
} from 'lucide-react';

interface SubjectDirectoryPageProps {
  subjects: SubjectSummary[];
  onSelectSubject: (subjectId: string) => void;
  onBackToOverview: () => void;
}

export const SubjectDirectoryPage: React.FC<SubjectDirectoryPageProps> = ({
  subjects,
  onSelectSubject,
  onBackToOverview
}) => {
  const [search, setSearch] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('all');

  const filteredSubjects = useMemo(() => {
    return subjects.filter((s) => {
      const matchSearch =
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.code.toLowerCase().includes(search.toLowerCase()) ||
        s.weakestTopic.toLowerCase().includes(search.toLowerCase());
      const matchSem = selectedSemester === 'all' || s.semester === selectedSemester;
      return matchSearch && matchSem;
    });
  }, [subjects, search, selectedSemester]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Header & Navigation */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#343434]">
        <div>
          <button
            onClick={onBackToOverview}
            className="inline-flex items-center space-x-1.5 text-xs text-[#B7B3B0] hover:text-[#C12A29] font-mono mb-2 transition-colors"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>Back to Class Overview</span>
          </button>

          <h1 className="text-2xl sm:text-3xl font-bold text-[#F5F2EF] tracking-tight">
            Curriculum Subject Directory
          </h1>
          <p className="text-xs sm:text-sm text-[#B7B3B0] mt-1">
            Department of Computer Science & Engineering • Multi-subject diagnostic reports
          </p>
        </div>

        {/* Search & Semester Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-[#898582] absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search subject or topic..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-[#171717] border border-[#343434] rounded-xl text-xs text-[#F5F2EF] placeholder-[#898582] focus:outline-none focus:ring-1 focus:ring-[#A31C1B] w-64"
            />
          </div>

          <select
            value={selectedSemester}
            onChange={(e) => setSelectedSemester(e.target.value)}
            className="py-2 px-3 bg-[#171717] border border-[#343434] rounded-xl text-xs text-[#F5F2EF] focus:outline-none focus:ring-1 focus:ring-[#A31C1B]"
          >
            <option value="all">All Semesters</option>
            <option value="Semester 3">Semester 3</option>
            <option value="Semester 4">Semester 4</option>
            <option value="Semester 5">Semester 5</option>
          </select>
        </div>
      </div>

      {/* 2. Subject Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredSubjects.map((subj) => {
          return (
            <div
              key={subj.id}
              onClick={() => onSelectSubject(subj.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectSubject(subj.id);
                }
              }}
              className="bg-[#202020] rounded-2xl border border-[#343434] hover:border-[#20372B] hover:bg-[#171717] p-6 shadow-sm transition-all cursor-pointer group flex flex-col justify-between"
              aria-label={`Subject ${subj.name} (${subj.code}). Overall average ${subj.overallAverage}%. Click to open report.`}
            >
              <div>
                {/* Top strip */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-[#171717] text-[#B7B3B0] border border-[#343434]">
                      {subj.code}
                    </span>
                    <span className="text-xs text-[#898582] font-mono">
                      {subj.semester}
                    </span>
                  </div>

                  {subj.isLiveDb ? (
                    <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-medium bg-[#0B1B14] text-emerald-300 border border-[#20372B]">
                      <Database className="w-3 h-3 text-emerald-400" />
                      <span>Live DB (PostgreSQL)</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[10px] font-mono font-medium bg-[#171717] text-[#898582] border border-[#343434]">
                      <Layers className="w-3 h-3" />
                      <span>Curriculum Active</span>
                    </span>
                  )}
                </div>

                {/* Subject Title */}
                <h3 className="text-xl font-bold text-[#F5F2EF] group-hover:text-white transition-colors">
                  {subj.name}
                </h3>
                <p className="text-xs text-[#B7B3B0] mt-1">
                  {subj.department} • {subj.studentCount} Students Enrolled
                </p>

                {/* Main Stats Bar */}
                <div className="grid grid-cols-2 gap-3 my-5">
                  <div className="p-3 bg-[#171717] rounded-xl border border-[#343434]">
                    <span className="text-[11px] font-mono text-[#898582] uppercase tracking-wider block">
                      Cohort Average
                    </span>
                    <span className="text-2xl font-bold font-mono text-[#F5F2EF] mt-0.5 block tabular-nums">
                      {subj.overallAverage}%
                    </span>
                    <span className="text-[10px] text-[#898582] font-mono">
                      Across {subj.topics.length} topics
                    </span>
                  </div>

                  <div className="p-3 bg-[#261214] rounded-xl border border-[#5C1D20]">
                    <span className="text-[11px] font-mono text-rose-300 uppercase tracking-wider block">
                      Acute Bottleneck
                    </span>
                    <span className="text-sm font-bold text-rose-200 mt-0.5 block truncate">
                      {subj.weakestTopic}
                    </span>
                    <span className="text-[11px] font-mono text-[#C12A29] font-semibold">
                      {subj.weakestMastery}% ({subj.interventionCount} students)
                    </span>
                  </div>
                </div>

                {/* Topics Mini-Pills */}
                <div className="space-y-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#898582] block">
                    Evaluated Concepts
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {subj.topics.map((t) => (
                      <span
                        key={t.id}
                        className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#171717] border border-[#343434] text-[#B7B3B0]"
                      >
                        {t.name} ({t.mastery}%)
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Footer */}
              <div className="mt-6 pt-4 border-t border-[#343434] flex items-center justify-between text-xs">
                <span className="text-[#898582] font-mono text-[11px]">
                  {subj.interventionCount} student intervention priority
                </span>
                <span className="text-[#C12A29] font-semibold flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
                  <span>View Full Subject Report</span>
                  <ArrowRight className="w-4 h-4" />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
