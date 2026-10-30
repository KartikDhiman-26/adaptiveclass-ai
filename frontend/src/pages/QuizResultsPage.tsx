import React from 'react';
import { 
  CheckCircle2, TrendingUp, Users, ArrowRight, Award, 
  Sparkles, School, RefreshCw, BarChart2, ShieldCheck 
} from 'lucide-react';
import { QuizSubmitResponse } from '../types';

interface QuizResultsPageProps {
  results: QuizSubmitResponse;
  onViewTeacherDashboard: () => void;
  onReturnToStudentDashboard: () => void;
}

export const QuizResultsPage: React.FC<QuizResultsPageProps> = ({
  results,
  onViewTeacherDashboard,
  onReturnToStudentDashboard
}) => {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
      {/* 1. Results Celebration Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-md text-center space-y-4 relative overflow-hidden">
        <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto shadow-inner">
          <Award className="w-8 h-8" />
        </div>

        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
            Practice Session Completed
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-2">
            Measurable Mastery Improvement!
          </h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
            Your adaptive practice performance has been computed and recorded in PostgreSQL.
          </p>
        </div>

        {/* Score metrics */}
        <div className="grid grid-cols-2 gap-4 max-w-md mx-auto pt-2">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-xs text-slate-500">Quiz Accuracy</span>
            <p className="text-2xl font-bold text-slate-900 mt-0.5">{results.accuracy}%</p>
            <span className="text-[11px] text-slate-400">({results.score} of {results.total_questions} correct)</span>
          </div>

          <div className="p-3 bg-indigo-50 rounded-xl border border-indigo-200">
            <span className="text-xs text-indigo-600 font-semibold">Mastery Gain</span>
            <p className="text-2xl font-bold text-indigo-700 mt-0.5">+{results.mastery_change}%</p>
            <span className="text-[11px] text-indigo-500 font-medium">Weighted Recalculation</span>
          </div>
        </div>

        {/* Before vs After Mastery Comparison */}
        <div className="p-4 bg-slate-900 text-white rounded-xl border border-slate-800 text-left max-w-lg mx-auto space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-300 font-medium">{results.concept_name} Mastery (Before):</span>
            <span className="text-sm font-bold text-rose-400">{results.old_mastery}% (Critical Gap)</span>
          </div>

          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div className="bg-rose-500 h-full rounded-full" style={{ width: `${results.old_mastery}%` }}></div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className="text-xs text-slate-300 font-medium">{results.concept_name} Mastery (After Practice):</span>
            <span className="text-base font-bold text-emerald-400">{results.new_mastery}% (Developing)</span>
          </div>

          <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full transition-all duration-700" style={{ width: `${results.new_mastery}%` }}></div>
          </div>
        </div>
      </div>

      {/* 2. THE "WOW" DEMO: Classroom-Level Closed Feedback Loop */}
      <div className="bg-gradient-to-br from-indigo-950 via-slate-900 to-indigo-950 text-white rounded-2xl p-6 shadow-lg border border-indigo-800/60 relative overflow-hidden">
        <div className="flex items-center space-x-2 text-xs font-bold text-indigo-300 uppercase tracking-wider mb-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span>Real-Time Classroom Impact</span>
        </div>

        <h3 className="text-xl font-bold text-white mb-2">
          Your Individual Practice Shifted the Entire Class Intelligence
        </h3>

        <p className="text-xs text-slate-300 leading-relaxed mb-4">
          Because student data is interconnected, your mastery gain crossed the 40% support threshold, directly improving the professor's live classroom metrics.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <span className="text-xs text-slate-300">Class {results.concept_name} Average</span>
            <div className="flex items-baseline space-x-2 mt-1">
              <span className="text-2xl font-black text-emerald-400">{results.new_class_recursion_average}%</span>
              <span className="text-xs text-slate-400">rose from 35.0%</span>
            </div>
            <p className="text-[11px] text-slate-300 mt-1">Recalculated from all 80 students in PostgreSQL</p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <span className="text-xs text-slate-300">Students Needing Support in Recursion</span>
            <div className="flex items-baseline space-x-2 mt-1">
              <span className="text-2xl font-black text-emerald-400">{results.new_recursion_support_count}</span>
              <span className="text-xs text-slate-400">decreased from 23!</span>
            </div>
            <p className="text-[11px] text-slate-300 mt-1">Aarav Sharma successfully uplifted</p>
          </div>
        </div>

        {/* Primary CTA: Switch back to Teacher Dashboard */}
        <div className="pt-4 border-t border-indigo-800/80 flex flex-col sm:flex-row items-center justify-between gap-3">
          <span className="text-xs text-slate-400">
            Click below to inspect the updated live Teacher Dashboard:
          </span>

          <button
            onClick={onViewTeacherDashboard}
            className="w-full sm:w-auto px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md hover:shadow-lg transition-all flex items-center justify-center space-x-2"
          >
            <School className="w-4 h-4" />
            <span>View Updated Teacher Dashboard</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>
        </div>
      </div>

      {/* Secondary Button */}
      <div className="text-center">
        <button
          onClick={onReturnToStudentDashboard}
          className="text-xs text-slate-500 hover:text-slate-800 font-semibold underline"
        >
          Return to Student Dashboard
        </button>
      </div>
    </div>
  );
};
