import React, { useState, useMemo } from 'react';
import { 
  AlertCircle, Award, TrendingUp, 
  AlertOctagon, RefreshCw, GraduationCap, Search, CheckCircle2
} from 'lucide-react';
import { ClassAnalyticsResponse, StudentNeedingAttentionItem, StudentProfileResponse } from '../types';
import { ConceptCard } from '../components/ConceptCard';
import { AiInsightCard } from '../components/AiInsightCard';
import { StudentProfileModal } from '../components/StudentProfileModal';
import { api } from '../api';

interface TeacherDashboardProps {
  analytics: ClassAnalyticsResponse | null;
  attentionStudents: StudentNeedingAttentionItem[];
  onRefresh: () => void;
  isLoading: boolean;
  onSimulateStudent: (studentId: number) => void;
}

export const TeacherDashboard: React.FC<TeacherDashboardProps> = ({
  analytics,
  attentionStudents,
  onRefresh,
  isLoading,
  onSimulateStudent
}) => {
  const [selectedStudentProfile, setSelectedStudentProfile] = useState<StudentProfileResponse | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [studentSearchQuery, setStudentSearchQuery] = useState('');

  const handleOpenStudentProfile = async (studentId: number) => {
    setIsLoadingProfile(true);
    try {
      const profile = await api.getStudentProfile(studentId);
      setSelectedStudentProfile(profile);
    } catch (err) {
      console.error("Failed to load student profile:", err);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  // Filter flagged students by search query
  const filteredAttentionStudents = useMemo(() => {
    if (!studentSearchQuery.trim()) return attentionStudents;
    const q = studentSearchQuery.toLowerCase();
    return attentionStudents.filter(s => 
      s.student_name.toLowerCase().includes(q) ||
      s.roll_number.toLowerCase().includes(q) ||
      s.weak_concept.toLowerCase().includes(q)
    );
  }, [attentionStudents, studentSearchQuery]);

  // 1. Loading Skeleton State
  if (isLoading && !analytics) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-pulse">
        {/* Masthead Skeleton */}
        <div className="bg-white rounded-2xl border border-stone-200 p-6 sm:p-7 shadow-sm">
          <div className="h-4 bg-stone-200 rounded w-48 mb-3" />
          <div className="h-8 bg-stone-200 rounded w-80 mb-2" />
          <div className="h-4 bg-stone-100 rounded w-96" />
        </div>

        {/* Ticker Skeleton */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(n => (
            <div key={n} className="bg-white rounded-xl border border-stone-200 p-5 h-24" />
          ))}
        </div>

        {/* AI Insight Skeleton */}
        <div className="bg-white rounded-2xl border border-stone-200 p-8 h-64" />

        {/* Concept Cards Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map(n => (
            <div key={n} className="bg-white rounded-xl border border-stone-200 p-5 h-36" />
          ))}
        </div>
      </div>
    );
  }

  // 2. Error Fallback State
  if (!analytics) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="bg-white rounded-2xl border border-stone-200 p-8 shadow-sm space-y-4">
          <div className="w-12 h-12 rounded-xl bg-red-50 text-red-700 flex items-center justify-center mx-auto">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-stone-900">Unable to Load Classroom Analytics</h2>
          <p className="text-sm text-stone-600 max-w-md mx-auto">
            Could not retrieve data from the backend or PostgreSQL instance. Please confirm the FastAPI server is running on port 8000.
          </p>
          <button
            onClick={() => onRefresh()}
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-stone-900 text-white text-xs font-semibold hover:bg-stone-800 transition-colors shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Database Connection</span>
          </button>
        </div>
      </div>
    );
  }

  // 3. Render Full Redesigned Teacher Dashboard
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. EDITORIAL MASTHEAD */}
      <header className="bg-white rounded-2xl border border-stone-200/90 p-6 sm:p-7 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-semibold uppercase tracking-widest text-stone-500 font-mono">
              Academic Term • {analytics.semester}
            </span>
            <span className="text-stone-300">•</span>
            <span className="text-[11px] text-stone-500 font-mono">Course ID #{analytics.class_id}</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-stone-900 tracking-tight mt-1.5">
            {analytics.class_name}
          </h1>

          <p className="text-xs sm:text-sm text-stone-600 mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
            <span>Subject: <strong className="text-stone-900 font-semibold">{analytics.subject}</strong></span>
            <span className="text-stone-300 hidden sm:inline">•</span>
            <span>Total Enrolled: <strong className="text-stone-900 font-semibold">{analytics.student_count} Students</strong></span>
            <span className="text-stone-300 hidden sm:inline">•</span>
            <span className="inline-flex items-center text-emerald-800 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mr-1.5 animate-pulse" />
              Live PostgreSQL Diagnostics Active
            </span>
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5 sm:self-center">
          <button
            onClick={() => onRefresh()}
            disabled={isLoading}
            aria-label="Refresh classroom analytics"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl border border-stone-200 text-xs font-medium text-stone-700 bg-stone-50 hover:bg-stone-100 hover:text-stone-900 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Recalculating...' : 'Refresh Metrics'}</span>
          </button>

          <button
            onClick={() => onSimulateStudent(1)} // Aarav Sharma (student@demo.com)
            title="Simulate Aarav Sharma taking an adaptive quiz in Recursion"
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-blue-900 hover:bg-blue-950 text-white text-xs font-semibold shadow-sm transition-all"
          >
            <GraduationCap className="w-4 h-4 text-blue-200" />
            <span>Simulate Student Loop</span>
          </button>
        </div>
      </header>

      {/* 2. EXECUTIVE METRIC SUMMARY BAR */}
      <section aria-label="Classroom Key Indicators">
        <div className="bg-white rounded-2xl border border-stone-200/90 shadow-sm overflow-hidden divide-y divide-stone-100 md:divide-y-0 md:divide-x md:divide-stone-200/90 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4">
          {/* Stat 1: Class Average */}
          <div className="p-5 sm:p-6 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                Cohort Average
              </span>
              <div className="w-7 h-7 rounded-lg bg-stone-100 text-stone-700 flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-blue-900" />
              </div>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold tracking-tight text-stone-900 tabular-nums">
                {analytics.overall_class_average}%
              </span>
              <span className="text-xs text-stone-500 font-normal">aggregate mastery</span>
            </div>
            <span className="text-[11px] text-stone-500 mt-2 block">
              Across 6 measured computational topics
            </span>
          </div>

          {/* Stat 2: Critical Learning Gap */}
          <div className="p-5 sm:p-6 flex flex-col justify-between bg-red-50/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-red-800">
                Primary Gap
              </span>
              <div className="w-7 h-7 rounded-lg bg-red-100 text-red-700 flex items-center justify-center">
                <AlertOctagon className="w-4 h-4" />
              </div>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl sm:text-3xl font-bold tracking-tight text-red-900">
                {analytics.weakest_concept}
              </span>
            </div>
            <span className="text-[11px] text-red-700 mt-2 block font-medium">
              Class mastery bottleneck (35.0%)
            </span>
          </div>

          {/* Stat 3: Academic Support Count */}
          <div className="p-5 sm:p-6 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                Support Group
              </span>
              <div className="w-7 h-7 rounded-lg bg-stone-100 text-stone-700 flex items-center justify-center">
                <AlertCircle className="w-4 h-4 text-amber-700" />
              </div>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold tracking-tight text-stone-900 tabular-nums">
                {analytics.recursion_support_count}
              </span>
              <span className="text-xs text-stone-500 font-normal">students</span>
            </div>
            <span className="text-[11px] text-stone-500 mt-2 block">
              Below the 40.0% foundational threshold
            </span>
          </div>

          {/* Stat 4: Advanced Learners */}
          <div className="p-5 sm:p-6 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
                Advanced Cohort
              </span>
              <div className="w-7 h-7 rounded-lg bg-stone-100 text-stone-700 flex items-center justify-center">
                <Award className="w-4 h-4 text-emerald-800" />
              </div>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold tracking-tight text-stone-900 tabular-nums">
                {analytics.global_distribution.advanced}
              </span>
              <span className="text-xs text-stone-500 font-normal">students</span>
            </div>
            <span className="text-[11px] text-emerald-800 font-medium mt-2 block">
              Demonstrating consistent high mastery (≥85%)
            </span>
          </div>
        </div>
      </section>

      {/* 3. INSTRUCTIONAL INTELLIGENCE BRIEFING (AI INSIGHT CARD) */}
      <AiInsightCard insight={analytics.ai_insight} />

      {/* 4. CURRICULAR CONCEPT MASTERY BREAKDOWN */}
      <section aria-labelledby="concept-matrix-heading" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 pb-1 border-b border-stone-200">
          <div>
            <h2 id="concept-matrix-heading" className="text-lg font-bold text-stone-900 tracking-tight">
              Curricular Competency Matrix
            </h2>
            <p className="text-xs text-stone-500 mt-0.5">
              Empirical mastery measured across all 80 students in PostgreSQL database
            </p>
          </div>
          <span className="text-xs font-mono text-stone-500">
            Benchmark: 40% (Remediation) • 75% (Proficiency)
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {analytics.concept_mastery.map((item) => (
            <ConceptCard
              key={item.concept_id}
              name={item.concept_name}
              percentage={item.mastery_percentage}
              statusLabel={item.status_label}
              statusColor={item.status_color}
            />
          ))}
        </div>
      </section>

      {/* 5. COHORT MASTERY SPECTRUM (STUDENT DISTRIBUTION) */}
      <section aria-labelledby="distribution-heading" className="bg-white rounded-2xl border border-stone-200/90 p-6 sm:p-7 shadow-sm space-y-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <h3 id="distribution-heading" className="text-base font-bold text-stone-900 tracking-tight">
              Cohort Distribution Spectrum
            </h3>
            <p className="text-xs text-stone-500 mt-0.5">
              Comprehensive distribution calculated across cumulative student mastery
            </p>
          </div>
          <span className="text-xs font-mono text-stone-600 bg-stone-100 px-2 py-0.5 rounded border border-stone-200">
            Total Roster: {analytics.global_distribution.total} Active Records
          </span>
        </div>

        {/* Clean Segmented Bar */}
        <div 
          role="img" 
          aria-label="Student performance distribution spectrum"
          className="w-full h-3.5 rounded-full bg-stone-100 flex overflow-hidden border border-stone-200/80 p-0.5"
        >
          <div
            title={`Advanced: ${analytics.global_distribution.advanced} students`}
            style={{ width: `${(analytics.global_distribution.advanced / analytics.global_distribution.total) * 100}%` }}
            className="h-full bg-emerald-600 rounded-l-full"
          />
          <div
            title={`On Track: ${analytics.global_distribution.on_track} students`}
            style={{ width: `${(analytics.global_distribution.on_track / analytics.global_distribution.total) * 100}%` }}
            className="h-full bg-blue-600"
          />
          <div
            title={`Needs Support: ${analytics.global_distribution.needs_support} students`}
            style={{ width: `${(analytics.global_distribution.needs_support / analytics.global_distribution.total) * 100}%` }}
            className="h-full bg-amber-500"
          />
          <div
            title={`Needs Attention: ${analytics.global_distribution.needs_attention} students`}
            style={{ width: `${(analytics.global_distribution.needs_attention / analytics.global_distribution.total) * 100}%` }}
            className="h-full bg-red-600 rounded-r-full"
          />
        </div>

        {/* Legend Grid with Tabular Counts */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-stone-100 text-xs">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 flex-shrink-0" />
              <span className="font-semibold text-stone-900">Advanced: {analytics.global_distribution.advanced}</span>
            </div>
            <p className="text-[11px] text-stone-500 font-mono pl-4.5">≥85% cumulative</p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600 flex-shrink-0" />
              <span className="font-semibold text-stone-900">On Track: {analytics.global_distribution.on_track}</span>
            </div>
            <p className="text-[11px] text-stone-500 font-mono pl-4.5">55% – 84% cumulative</p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 flex-shrink-0" />
              <span className="font-semibold text-stone-900">Needs Support: {analytics.global_distribution.needs_support}</span>
            </div>
            <p className="text-[11px] text-stone-500 font-mono pl-4.5">40% – 54% cumulative</p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-600 flex-shrink-0" />
              <span className="font-semibold text-stone-900">Needs Attention: {analytics.global_distribution.needs_attention}</span>
            </div>
            <p className="text-[11px] text-stone-500 font-mono pl-4.5">&lt;40% acute deficit</p>
          </div>
        </div>
      </section>

      {/* 6. STUDENTS NEEDING ATTENTION & ENRICHMENT SIDEBAR */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Table (2 Columns) */}
        <section aria-labelledby="attention-table-heading" className="lg:col-span-2 bg-white rounded-2xl border border-stone-200/90 p-6 sm:p-7 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
              <div>
                <h3 id="attention-table-heading" className="text-base font-bold text-stone-900 tracking-tight">
                  Students Requiring Academic Attention
                </h3>
                <p className="text-xs text-stone-500 mt-0.5">
                  Cohort members exhibiting acute concept deficits below the 40% support bar
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-stone-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search student or concept..."
                    value={studentSearchQuery}
                    onChange={(e) => setStudentSearchQuery(e.target.value)}
                    className="pl-8 pr-3 py-1.5 border border-stone-200 rounded-lg text-xs w-48 sm:w-56 bg-stone-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-900"
                  />
                </div>
                <span className="text-xs bg-red-50 border border-red-200/80 text-red-800 font-semibold px-2 py-1 rounded">
                  {attentionStudents.length} Flagged
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-stone-50 text-stone-600 uppercase font-semibold text-[11px] border-y border-stone-200">
                    <th className="py-2.5 px-3">Student Name</th>
                    <th className="py-2.5 px-3">Primary Deficit</th>
                    <th className="py-2.5 px-3">Mastery</th>
                    <th className="py-2.5 px-3">Recommended Intervention</th>
                    <th className="py-2.5 px-3 text-right">Diagnostic</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {filteredAttentionStudents.length > 0 ? (
                    filteredAttentionStudents.slice(0, 7).map((s) => (
                      <tr key={s.student_id} className="hover:bg-stone-50/70 transition-colors">
                        <td className="py-3 px-3">
                          <div className="font-semibold text-stone-900">{s.student_name}</div>
                          <div className="text-[11px] text-stone-500 font-mono">{s.roll_number}</div>
                        </td>
                        <td className="py-3 px-3">
                          <span className="inline-block font-medium text-red-800 bg-red-50 px-2 py-0.5 rounded border border-red-200/70">
                            {s.weak_concept}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-mono font-bold text-stone-900 tabular-nums">
                          {s.mastery}%
                        </td>
                        <td className="py-3 px-3 text-stone-700">
                          {s.recommended_action}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <button
                            onClick={() => handleOpenStudentProfile(s.student_id)}
                            disabled={isLoadingProfile}
                            className="text-xs font-semibold text-blue-900 hover:text-blue-950 bg-blue-50 hover:bg-blue-100/70 px-2.5 py-1 rounded-md border border-blue-200/60 transition-colors"
                          >
                            Inspect Profile
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-stone-500 text-xs">
                        {studentSearchQuery ? (
                          <span>No students found matching "{studentSearchQuery}".</span>
                        ) : (
                          <div className="flex flex-col items-center justify-center space-y-1">
                            <CheckCircle2 className="w-5 h-5 text-emerald-600 mb-1" />
                            <span className="font-semibold text-stone-800">All students performing above support bar</span>
                            <span className="text-[11px]">No active students currently fall below the 40% support threshold.</span>
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="pt-4 border-t border-stone-100 text-[11px] text-stone-500 flex justify-between items-center">
            <span>Displaying priority cohort entries • Sorted by acute deficit</span>
            <span className="font-mono">Threshold: &lt;40%</span>
          </div>
        </section>

        {/* Advanced Scholars Enrichment Track (1 Column) */}
        <aside aria-label="Advanced Enrichment Overview" className="bg-[#FAF9F6] rounded-2xl border border-stone-200/90 p-6 sm:p-7 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-stone-700 mb-2">
              <Award className="w-4 h-4 text-stone-800" />
              <span>High-Mastery Cohort</span>
            </div>

            <h4 className="text-xl font-bold text-stone-900 tracking-tight mb-2">
              {analytics.global_distribution.advanced} Scholars Excel
            </h4>

            <p className="text-xs text-stone-600 leading-relaxed mb-4">
              Adaptive pacing ensures advanced students are challenged with high-order algorithmic extensions while struggling peers receive foundation reinforcement.
            </p>

            <div className="bg-white border border-stone-200 rounded-xl p-4 space-y-2.5 text-xs">
              <span className="font-semibold text-stone-900 block">Curricular Extension Challenges:</span>
              <ul className="space-y-2 text-stone-700">
                <li className="flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-stone-400 mt-1.5 flex-shrink-0" />
                  <span>AVL tree double-rotations & self-balancing properties</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-stone-400 mt-1.5 flex-shrink-0" />
                  <span>Dijkstra vs Bellman-Ford shortest-path edge cases</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-stone-400 mt-1.5 flex-shrink-0" />
                  <span>Cycle detection via Tarjan's Strongly Connected Components</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-stone-200">
            <button
              onClick={() => onSimulateStudent(1)} // Aarav Sharma
              className="w-full bg-stone-900 hover:bg-stone-800 text-white text-xs font-bold py-2.5 px-4 rounded-xl flex items-center justify-center space-x-2 shadow-sm transition-colors"
            >
              <GraduationCap className="w-4 h-4 text-stone-300" />
              <span>Launch Aarav's Practice Session</span>
            </button>
            <p className="text-[10px] text-stone-500 text-center mt-2">
              1-click test of the 5-step adaptive feedback loop
            </p>
          </div>
        </aside>
      </div>

      {/* Student Profile Modal Drilldown */}
      <StudentProfileModal
        profile={selectedStudentProfile}
        onClose={() => setSelectedStudentProfile(null)}
        onSimulateStudentPractice={(studentId) => {
          setSelectedStudentProfile(null);
          onSimulateStudent(studentId);
        }}
      />
    </div>
  );
};
