import React, { useState } from 'react';
import { 
  Users, AlertCircle, Award, TrendingUp, Sparkles, 
  ChevronRight, ArrowUpRight, CheckCircle2, AlertOctagon,
  RefreshCw, GraduationCap
} from 'lucide-react';
import { ClassAnalyticsResponse, StudentNeedingAttentionItem, StudentProfileResponse } from '../types';
import { ConceptCard } from '../components/ConceptCard';
import { AiInsightCard } from '../components/AiInsightCard';
import { StudentProfileModal } from '../components/StudentProfileModal';
import { api } from '../api';

interface TeacherDashboardProps {
  analytics: ClassAnalyticsResponse;
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Header Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold border border-indigo-200">
              {analytics.semester}
            </span>
            <span className="text-slate-400 text-xs">•</span>
            <span className="text-xs text-slate-500 font-medium">Class ID: #{analytics.class_id}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mt-1">
            {analytics.class_name}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Subject: <strong className="text-slate-700">{analytics.subject}</strong> • Total Enrolled: <strong className="text-slate-700">{analytics.student_count} Students</strong>
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refetch Live Analytics</span>
          </button>
        </div>
      </div>

      {/* 2. Top Stats Overview Bar */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium">Class Average</span>
            <p className="text-xl font-bold text-slate-900">{analytics.overall_class_average}%</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
            <AlertOctagon className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-rose-600 font-medium">Critical Learning Gap</span>
            <p className="text-xl font-bold text-slate-900">{analytics.weakest_concept}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-amber-700 font-medium">Recursion Support</span>
            <p className="text-xl font-bold text-slate-900">{analytics.recursion_support_count} Students</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-emerald-700 font-medium">Advanced Learners</span>
            <p className="text-xl font-bold text-slate-900">{analytics.global_distribution.advanced} Students</p>
          </div>
        </div>
      </div>

      {/* 3. PROMINENT AI CLASSROOM INSIGHT (Most Important Element) */}
      <AiInsightCard insight={analytics.ai_insight} />

      {/* 4. Concept Mastery Breakdown Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Class Concept Understanding</h2>
            <p className="text-xs text-slate-500">Calculated across 80 students in PostgreSQL</p>
          </div>
          <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-100">
            6 Concepts Measured
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
      </div>

      {/* 5. Student Learning Status Distribution */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Student Learning Status Distribution</h3>
            <p className="text-xs text-slate-500">Based on overall academic performance across all 6 concepts</p>
          </div>
          <span className="text-xs text-slate-400">Total: {analytics.global_distribution.total} Students</span>
        </div>

        {/* Segmented Bar */}
        <div className="w-full h-4 rounded-full bg-slate-100 flex overflow-hidden p-0.5 border border-slate-200">
          <div
            title={`Advanced: ${analytics.global_distribution.advanced} students`}
            style={{ width: `${(analytics.global_distribution.advanced / 80) * 100}%` }}
            className="h-full bg-emerald-500 rounded-l-full"
          ></div>
          <div
            title={`On Track: ${analytics.global_distribution.on_track} students`}
            style={{ width: `${(analytics.global_distribution.on_track / 80) * 100}%` }}
            className="h-full bg-blue-500"
          ></div>
          <div
            title={`Needs Support: ${analytics.global_distribution.needs_support} students`}
            style={{ width: `${(analytics.global_distribution.needs_support / 80) * 100}%` }}
            className="h-full bg-amber-500"
          ></div>
          <div
            title={`Needs Attention: ${analytics.global_distribution.needs_attention} students`}
            style={{ width: `${(analytics.global_distribution.needs_attention / 80) * 100}%` }}
            className="h-full bg-rose-500 rounded-r-full"
          ></div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 pt-4 border-t border-slate-100 text-xs">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500 flex-shrink-0"></span>
            <div>
              <span className="font-semibold text-slate-800">Advanced: {analytics.global_distribution.advanced}</span>
              <p className="text-[11px] text-slate-400">≥85% overall</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-blue-500 flex-shrink-0"></span>
            <div>
              <span className="font-semibold text-slate-800">On Track: {analytics.global_distribution.on_track}</span>
              <p className="text-[11px] text-slate-400">55% - 84% overall</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-amber-500 flex-shrink-0"></span>
            <div>
              <span className="font-semibold text-slate-800">Needs Support: {analytics.global_distribution.needs_support}</span>
              <p className="text-[11px] text-slate-400">40% - 54% overall</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-rose-500 flex-shrink-0"></span>
            <div>
              <span className="font-semibold text-slate-800">Needs Attention: {analytics.global_distribution.needs_attention}</span>
              <p className="text-[11px] text-slate-400">&lt;40% overall</p>
            </div>
          </div>
        </div>
      </div>

      {/* 6. Students Needing Attention Table & Advanced Enrichment Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table: Students Needing Attention (2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Students Needing Academic Attention</h3>
              <p className="text-xs text-slate-500">Students with acute concept deficits below the support threshold</p>
            </div>
            <span className="text-xs bg-rose-50 border border-rose-200 text-rose-700 font-semibold px-2 py-0.5 rounded">
              {attentionStudents.length} Students Flagged
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-y border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Student</th>
                  <th className="py-2.5 px-3">Weak Concept</th>
                  <th className="py-2.5 px-3">Mastery</th>
                  <th className="py-2.5 px-3">Recommended Action</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {attentionStudents.slice(0, 7).map((s) => (
                  <tr key={s.student_id} className="hover:bg-slate-50/80 transition-colors group">
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-900">{s.student_name}</div>
                      <div className="text-[11px] text-slate-400">{s.roll_number}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-medium text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                        {s.weak_concept}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold text-slate-800">
                      {s.mastery}%
                    </td>
                    <td className="py-3 px-3 text-slate-600">
                      {s.recommended_action}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => handleOpenStudentProfile(s.student_id)}
                        className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded transition-colors"
                      >
                        View Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Advanced Learners Enrichment Panel (1 Col) */}
        <div className="bg-slate-900 text-white rounded-2xl border border-slate-800 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2">
              <Award className="w-4 h-4" />
              <span>Advanced Learners Enrichment</span>
            </div>

            <h4 className="text-lg font-bold text-white mb-2">
              {analytics.global_distribution.advanced} Students Consistently Excel
            </h4>

            <p className="text-xs text-slate-300 leading-relaxed mb-4">
              Adaptive learning ensures high performers are not held back while the rest of the class revises recursion.
            </p>

            <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3.5 space-y-2 text-xs">
              <span className="font-semibold text-indigo-300">Suggested Enrichment Challenges:</span>
              <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
                <li>AVL Tree double-rotation implementations</li>
                <li>Dijkstra vs Bellman-Ford complexity analysis</li>
                <li>Competitive programming dynamic programming sets</li>
                <li>Graph cycle detection using Tarjan's SCC</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800">
            <button
              onClick={() => onSimulateStudent(1)} // Aarav Sharma
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2.5 px-4 rounded-xl flex items-center justify-center space-x-2 shadow-md transition-colors"
            >
              <GraduationCap className="w-4 h-4" />
              <span>Simulate Aarav's Practice Loop</span>
            </button>
          </div>
        </div>
      </div>

      {/* Student Profile Modal */}
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
