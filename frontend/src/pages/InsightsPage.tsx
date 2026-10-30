import React, { useState } from 'react';
import { SubjectSummary } from '../types';
import { 
  ShieldCheck, ArrowRight, GraduationCap
} from 'lucide-react';

interface InsightsPageProps {
  subjects: SubjectSummary[];
  onOpenSubjectReport: (subjectId: string) => void;
  onSimulatePractice: (studentId: number) => void;
}

export const InsightsPage: React.FC<InsightsPageProps> = ({
  subjects,
  onOpenSubjectReport,
  onSimulatePractice
}) => {
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'critical' | 'strengths'>('all');

  // Collect prioritized intervention list
  const interventionList = subjects.map((subj) => ({
    subject: subj,
    weakTopic: subj.weakestTopic,
    mastery: subj.weakestMastery,
    studentsAffected: subj.interventionCount,
    action: subj.instructionalRecommendations.action,
    rationale: subj.instructionalRecommendations.rationale,
    urgency: subj.weakestMastery < 40 ? 'High' : 'Medium'
  })).sort((a, b) => a.mastery - b.mastery);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Insights Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#343434]">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#C12A29] font-semibold">
              Curricular Intelligence Engine
            </span>
            <span className="text-[#898582]">•</span>
            <span className="text-xs text-[#B7B3B0]">Continuous Pedagogical Diagnostics</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-[#F5F2EF] tracking-tight mt-1">
            Learning Gaps & Intervention Priorities
          </h1>
          <p className="text-xs sm:text-sm text-[#B7B3B0] mt-1">
            Evidence-based prescriptive guidance across 4 engineering subjects and 80 enrolled students
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 bg-[#171717] p-1 rounded-xl border border-[#343434] text-xs">
          <button
            onClick={() => setSelectedFilter('all')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              selectedFilter === 'all'
                ? 'bg-[#A31C1B] text-white font-semibold'
                : 'text-[#B7B3B0] hover:text-[#F5F2EF]'
            }`}
          >
            All Action Directives ({interventionList.length})
          </button>
          <button
            onClick={() => setSelectedFilter('critical')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              selectedFilter === 'critical'
                ? 'bg-[#261214] text-rose-300 border border-[#5C1D20] font-semibold'
                : 'text-[#B7B3B0] hover:text-[#F5F2EF]'
            }`}
          >
            Critical Gaps (&lt;40%)
          </button>
        </div>
      </div>

      {/* 2. Top Banner: Explainable Diagnostic Directive */}
      <section aria-label="Priority Action Directive">
        <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 sm:p-7 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-[#A31C1B] animate-pulse" />
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#C12A29] font-semibold">
                Class-wide Critical Bottleneck Isolated
              </span>
            </div>
            <span className="text-xs font-mono text-[#898582]">PostgreSQL Analytical Synthesis</span>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-baseline justify-between gap-4">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-[#F5F2EF]">
                Data Structures: Recursion Base Case Deficit (35.0% Class Average)
              </h2>
              <p className="text-xs sm:text-sm text-[#B7B3B0] mt-1.5 max-w-3xl leading-relaxed">
                Empirical quiz and assessment records indicate that <strong>23 out of 80 students</strong> fail to correctly identify termination conditions for recursive algorithms, triggering runtime infinite execution misconceptions.
              </p>
            </div>

            <button
              onClick={() => onSimulatePractice(1)}
              className="px-4 py-2.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] text-white font-semibold text-xs transition-colors flex items-center space-x-2 flex-shrink-0"
            >
              <GraduationCap className="w-4 h-4" />
              <span>Simulate Aarav Sharma Loop</span>
            </button>
          </div>

          {/* Action & Rationale Split */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-2">
            <div className="p-4 bg-[#171717] rounded-xl border border-[#343434] space-y-1.5">
              <span className="text-amber-400 font-mono font-semibold uppercase tracking-wider text-[10px] block">
                Recommended Pedagogical Intervention
              </span>
              <p className="text-[#B7B3B0] leading-relaxed">
                Dedicate the first 20 minutes of tomorrow's lecture to physical stack frame tracing with index bounds, contrasting iterative loops against recursive unwinding.
              </p>
            </div>

            <div className="p-4 bg-[#171717] rounded-xl border border-[#343434] space-y-1.5">
              <span className="text-[#C12A29] font-mono font-semibold uppercase tracking-wider text-[10px] block">
                Evidence & Diagnostic Basis
              </span>
              <p className="text-[#B7B3B0] leading-relaxed">
                Students attempting the adaptive quiz averaged only 1.2 / 5 correct answers on tree traversal and base case detection, compared to 4.1 / 5 on contiguous arrays.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Ranked Intervention Priority Stack */}
      <section aria-label="Intervention Stack" className="space-y-4">
        <h2 className="text-lg font-bold text-[#F5F2EF]">
          Ranked Intervention Priority Matrix
        </h2>

        <div className="space-y-4">
          {interventionList.map((item, idx) => {
            return (
              <div
                key={item.subject.id}
                className="bg-[#202020] rounded-xl border border-[#343434] p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-[#20372B] hover:bg-[#171717] transition-all"
              >
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 rounded-lg bg-[#171717] border border-[#343434] text-[#B7B3B0] font-mono font-bold flex items-center justify-center text-xs flex-shrink-0">
                    0{idx + 1}
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-[#171717] text-[#B7B3B0] border border-[#343434]">
                        {item.subject.code}
                      </span>
                      <h3 className="text-sm font-bold text-[#F5F2EF]">
                        {item.subject.name}
                      </h3>
                      {item.subject.isLiveDb && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0B1B14] text-emerald-300 border border-[#20372B]">
                          Live DB
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-[#B7B3B0]">
                      Acute Deficit: <strong className="text-[#C12A29]">{item.weakTopic}</strong> at <strong className="font-mono text-[#F5F2EF]">{item.mastery}%</strong> ({item.studentsAffected} students flagged)
                    </p>

                    <p className="text-xs text-[#898582] leading-relaxed max-w-2xl">
                      Action: {item.action}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 sm:self-center flex-shrink-0">
                  <button
                    onClick={() => onOpenSubjectReport(item.subject.id)}
                    className="px-3.5 py-2 rounded-xl bg-[#171717] hover:bg-[#202020] border border-[#343434] text-xs text-[#C12A29] font-medium transition-colors flex items-center space-x-1.5"
                  >
                    <span>View Subject Details</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 4. Teacher Agency Statement */}
      <footer className="p-4 bg-[#0B1B14] rounded-xl border border-[#20372B] flex items-center space-x-3 text-xs text-[#B7B3B0]">
        <ShieldCheck className="w-5 h-5 text-[#C12A29] flex-shrink-0" />
        <span>
          <strong>Pedagogical Assurance:</strong> AdaptiveClass AI surfaces empirical student telemetry to empower instructor discretion. AI assists diagnostics; the professor directs pedagogy.
        </span>
      </footer>
    </div>
  );
};
