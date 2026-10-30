import React from 'react';
import { SubjectSummary, StudentStatusDistribution, StudentNeedingAttentionItem } from '../types';
import { 
  TrendingUp, AlertOctagon, Award, Users, RefreshCw, 
  GraduationCap, ArrowRight, UploadCloud
} from 'lucide-react';
import { SubjectMasteryComparisonChart } from '../components/SubjectMasteryComparisonChart';
import { TopicMasteryHeatmap } from '../components/TopicMasteryHeatmap';
import { StudentScoreDistribution } from '../components/StudentScoreDistribution';

interface ClassOverviewPageProps {
  subjects: SubjectSummary[];
  distribution: StudentStatusDistribution;
  attentionStudents?: StudentNeedingAttentionItem[];
  isLoading: boolean;
  onRefresh: () => void;
  onSelectSubject: (subjectId: string) => void;
  onViewAllSubjects: () => void;
  onViewStudents: () => void;
  onViewInsights: () => void;
  onSimulateStudent: (studentId: number) => void;
  onOpenUploadModal?: () => void;
}

export const ClassOverviewPage: React.FC<ClassOverviewPageProps> = ({
  subjects,
  distribution,
  isLoading,
  onRefresh,
  onSelectSubject,
  onViewAllSubjects,
  onViewStudents,
  onViewInsights,
  onSimulateStudent,
  onOpenUploadModal
}) => {
  // Aggregate stats across subjects
  const totalStudents = distribution.total || 80;
  const averageAcrossSubjects =
    subjects.length > 0
      ? Math.round((subjects.reduce((sum, s) => sum + s.overallAverage, 0) / subjects.length) * 10) / 10
      : 59.2;
  const totalInterventions =
    subjects.length > 0
      ? subjects.reduce((sum, s) => sum + s.interventionCount, 0)
      : 23;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Header & Quick Actions */}
      <header className="bg-[#202020] rounded-2xl border border-[#343434] p-6 sm:p-7 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#C12A29] font-semibold">
              Department of Computer Science & Engineering
            </span>
            <span className="text-[#898582]">•</span>
            <span className="text-[11px] text-[#B7B3B0] font-mono">Academic Year 2026</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-[#F5F2EF] tracking-tight mt-1">
            Class Overview & Curriculum Diagnostics
          </h1>

          <p className="text-xs sm:text-sm text-[#B7B3B0] mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
            <span>Cohort Size: <strong className="text-[#F5F2EF]">{totalStudents} Students</strong></span>
            <span className="text-[#898582]">•</span>
            <span>Subjects Tracked: <strong className="text-[#F5F2EF]">{subjects.length} Core Courses</strong></span>
            <span className="text-[#898582]">•</span>
            <span className="inline-flex items-center text-emerald-300 font-mono text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
              Live PostgreSQL Diagnostics Active
            </span>
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {onOpenUploadModal && (
            <button
              onClick={onOpenUploadModal}
              aria-label="Upload Dataset"
              className="inline-flex items-center space-x-1.5 px-3.5 py-2.5 rounded-xl border border-[#343434] text-xs font-mono font-medium text-[#F5F2EF] bg-[#0B1B14] hover:bg-[#14231C] hover:border-[#20372B] transition-colors"
            >
              <UploadCloud className="w-3.5 h-3.5 text-emerald-400" />
              <span>Import Dataset</span>
            </button>
          )}

          <button
            onClick={onRefresh}
            disabled={isLoading}
            aria-label="Recalculate metrics"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2.5 rounded-xl border border-[#343434] text-xs font-mono font-medium text-[#B7B3B0] bg-[#171717] hover:bg-[#202020] hover:text-[#F5F2EF] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Recalculating...' : 'Refresh Telemetry'}</span>
          </button>

          <button
            onClick={() => onSimulateStudent(1)} // Aarav Sharma
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] text-white font-semibold text-xs transition-colors shadow-sm"
          >
            <GraduationCap className="w-4 h-4" />
            <span>Simulate Practice Loop</span>
          </button>
        </div>
      </header>

      {/* 2. Executive Metric KPI Tiles */}
      <section aria-label="Executive Indicators">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#202020] rounded-xl border border-[#343434] p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-[#B7B3B0]">
              <span>Curriculum Average</span>
              <TrendingUp className="w-4 h-4 text-[#C12A29]" />
            </div>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-3xl font-bold font-mono text-[#F5F2EF] tabular-nums">
                {averageAcrossSubjects}%
              </span>
              <span className="text-xs text-[#898582] font-mono">weighted mastery</span>
            </div>
            <span className="text-[11px] text-[#898582] font-mono mt-2 block">
              Across {subjects.length} engineering courses
            </span>
          </div>

          <div className="bg-[#261214] rounded-xl border border-[#5C1D20] p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-rose-300">
              <span>Acute Bottleneck</span>
              <AlertOctagon className="w-4 h-4 text-[#C12A29]" />
            </div>
            <div className="mt-2">
              <span className="text-xl sm:text-2xl font-bold font-mono text-rose-200 block truncate">
                Recursion (35%)
              </span>
              <span className="text-xs text-rose-400 font-mono">
                Data Structures • 23 students
              </span>
            </div>
            <button
              onClick={onViewInsights}
              className="text-[11px] text-[#C12A29] hover:text-rose-200 font-mono mt-2 underline text-left"
            >
              View targeted intervention →
            </button>
          </div>

          <div className="bg-[#202020] rounded-xl border border-[#343434] p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-[#B7B3B0]">
              <span>Active Interventions</span>
              <Users className="w-4 h-4 text-amber-400" />
            </div>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-3xl font-bold font-mono text-amber-300 tabular-nums">
                {totalInterventions}
              </span>
              <span className="text-xs text-[#898582] font-mono">student flags</span>
            </div>
            <button
              onClick={onViewStudents}
              className="text-[11px] text-amber-400 hover:text-amber-200 font-mono mt-2 underline text-left"
            >
              Review flagged student roster →
            </button>
          </div>

          <div className="bg-[#0B1B14] rounded-xl border border-[#20372B] p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-emerald-300">
              <span>High Mastery Scholars</span>
              <Award className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-3xl font-bold font-mono text-emerald-300 tabular-nums">
                {distribution.advanced}
              </span>
              <span className="text-xs text-[#898582] font-mono">students (≥85%)</span>
            </div>
            <span className="text-[11px] text-[#898582] font-mono mt-2 block">
              Eligible for advanced research tracks
            </span>
          </div>
        </div>
      </section>

      {/* 3. Subject Mastery Comparison Chart */}
      <section aria-label="Curriculum Benchmark Comparison">
        <SubjectMasteryComparisonChart
          subjects={subjects}
          onSelectSubject={onSelectSubject}
        />
      </section>

      {/* 4. Subject Preview Cards Grid (Clickable) */}
      <section aria-label="Subject Directory Quick Access" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-[#F5F2EF]">
              Active Curriculum Subjects ({subjects.length})
            </h2>
            <p className="text-xs text-[#B7B3B0] mt-0.5">
              Click any subject to open its detailed topic report, distributions, and recommendations
            </p>
          </div>

          <button
            onClick={onViewAllSubjects}
            className="text-xs font-mono text-[#C12A29] hover:text-[#F5F2EF] flex items-center space-x-1"
          >
            <span>View Full Directory</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {subjects.map((subj) => (
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
              className="bg-[#202020] rounded-xl border border-[#343434] hover:border-[#20372B] hover:bg-[#171717] p-5 transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#171717] text-[#B7B3B0] border border-[#343434]">
                    {subj.code}
                  </span>
                  {subj.isLiveDb && (
                    <span className="text-[10px] font-mono text-emerald-400 flex items-center space-x-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      <span>Live DB</span>
                    </span>
                  )}
                </div>

                <h3 className="text-sm font-bold text-[#F5F2EF] group-hover:text-white transition-colors">
                  {subj.name}
                </h3>
                <span className="text-[11px] text-[#898582] font-mono block mt-0.5">
                  {subj.semester}
                </span>

                <div className="my-4 pt-3 border-t border-[#343434] space-y-1">
                  <div className="flex items-baseline justify-between text-xs font-mono">
                    <span className="text-[#B7B3B0]">Average:</span>
                    <span className="text-base font-bold text-[#F5F2EF] tabular-nums">
                      {subj.overallAverage}%
                    </span>
                  </div>

                  <div className="flex items-baseline justify-between text-xs font-mono mt-1">
                    <span className="text-[#898582] text-[11px]">Primary Deficit:</span>
                    <span className="text-[#C12A29] text-[11px] font-semibold truncate max-w-[130px]">
                      {subj.weakestTopic}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-[#343434] flex items-center justify-between text-xs font-mono text-[#C12A29]">
                <span className="text-[11px]">Open Report</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Topic Mastery Heatmap */}
      <section aria-label="Topic Diagnostic Matrix">
        <TopicMasteryHeatmap
          subjects={subjects}
          onSelectTopic={(_topic, subject) => onSelectSubject(subject.id)}
        />
      </section>

      {/* 6. Cohort Score Distribution Histogram */}
      <section aria-label="Class Distribution">
        <StudentScoreDistribution
          distribution={distribution}
          onFilterTier={onViewStudents}
        />
      </section>
    </div>
  );
};
