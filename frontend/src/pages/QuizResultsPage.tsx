import React from 'react';
import { 
  ArrowRight, Award, Sparkles, School
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
      <div className="bg-[#202020] rounded-2xl border border-[#343434] p-8 shadow-xl text-center space-y-4 relative overflow-hidden">
        <div className="w-16 h-16 rounded-2xl bg-[#0B1B14] border border-[#20372B] text-emerald-400 flex items-center justify-center mx-auto shadow-inner">
          <Award className="w-8 h-8" />
        </div>

        <div>
          <span className="text-xs font-bold uppercase font-mono tracking-wider text-emerald-300 bg-[#0B1B14] px-3 py-1 rounded-full border border-[#20372B]">
            Practice Session Completed
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F5F2EF] mt-2">
            Measurable Mastery Improvement!
          </h2>
          <p className="text-sm text-[#B7B3B0] max-w-md mx-auto mt-1 font-mono">
            Your adaptive practice performance has been computed and recorded in PostgreSQL.
          </p>
        </div>

        {/* Score metrics */}
        <div className="grid grid-cols-2 gap-4 max-w-md mx-auto pt-2">
          <div className="p-3 bg-[#171717] rounded-xl border border-[#343434] font-mono">
            <span className="text-xs text-[#898582]">Quiz Accuracy</span>
            <p className="text-2xl font-bold text-[#F5F2EF] mt-0.5 tabular-nums">{results.accuracy}%</p>
            <span className="text-[11px] text-[#898582]">({results.score} of {results.total_questions} correct)</span>
          </div>

          <div className="p-3 bg-[#0B1B14] rounded-xl border border-[#20372B] font-mono">
            <span className="text-xs text-emerald-400 font-semibold">Mastery Gain</span>
            <p className="text-2xl font-bold text-emerald-300 mt-0.5 tabular-nums">+{results.mastery_change}%</p>
            <span className="text-[11px] text-emerald-400/80 font-medium">Weighted Recalculation</span>
          </div>
        </div>

        {/* Before vs After Mastery Comparison */}
        <div className="p-4 bg-[#171717] text-[#F5F2EF] rounded-xl border border-[#343434] text-left max-w-lg mx-auto space-y-3 font-mono">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#898582] font-medium">{results.concept_name} Mastery (Before):</span>
            <span className="font-bold text-[#C12A29]">{results.old_mastery}% (Critical Gap)</span>
          </div>

          <div className="w-full bg-[#06110C] rounded-full h-2 overflow-hidden border border-[#343434]">
            <div className="bg-[#A31C1B] h-full rounded-full" style={{ width: `${results.old_mastery}%` }} />
          </div>

          <div className="flex items-center justify-between pt-1 text-xs">
            <span className="text-[#898582] font-medium">{results.concept_name} Mastery (After Practice):</span>
            <span className="font-bold text-emerald-300">{results.new_mastery}% (Developing)</span>
          </div>

          <div className="w-full bg-[#06110C] rounded-full h-2.5 overflow-hidden border border-[#343434]">
            <div className="bg-emerald-400 h-full rounded-full transition-all duration-700" style={{ width: `${results.new_mastery}%` }} />
          </div>
        </div>
      </div>

      {/* 2. Closed Feedback Loop Impact Card */}
      <div className="bg-[#202020] text-[#F5F2EF] rounded-2xl p-6 sm:p-7 shadow-xl border border-[#343434] relative overflow-hidden">
        <div className="flex items-center space-x-2 text-xs font-bold font-mono text-[#C12A29] uppercase tracking-wider mb-2">
          <Sparkles className="w-4 h-4 text-[#C12A29]" />
          <span>Real-Time Classroom Impact</span>
        </div>

        <h3 className="text-xl font-bold text-[#F5F2EF] mb-2">
          Your Individual Practice Shifted the Entire Class Intelligence
        </h3>

        <p className="text-xs text-[#B7B3B0] leading-relaxed mb-4">
          Because student data is interconnected, your mastery gain crossed the 40% support threshold, directly improving the professor's live classroom metrics.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-4">
          <div className="bg-[#171717] rounded-xl p-4 border border-[#343434] font-mono">
            <span className="text-xs text-[#898582]">Class {results.concept_name} Average</span>
            <div className="flex items-baseline space-x-2 mt-1">
              <span className="text-2xl font-bold text-emerald-300 tabular-nums">{results.new_class_recursion_average}%</span>
              <span className="text-xs text-[#898582]">Live cohort average</span>
            </div>
            <p className="text-[11px] text-[#898582] mt-1 font-sans">Recalculated in PostgreSQL across active students</p>
          </div>

          <div className="bg-[#171717] rounded-xl p-4 border border-[#343434] font-mono">
            <span className="text-xs text-[#898582]">Students Needing Support in {results.concept_name}</span>
            <div className="flex items-baseline space-x-2 mt-1">
              <span className="text-2xl font-bold text-[#C12A29] tabular-nums">{results.new_recursion_support_count}</span>
              <span className="text-xs text-[#898582]">students &lt; 40%</span>
            </div>
            <p className="text-[11px] text-[#898582] mt-1 font-sans">Threshold alerts updated in real-time</p>
          </div>
        </div>

        <p className="text-xs text-[#898582] font-mono italic">
          💡 {results.impact_message}
        </p>

        {/* Action Doors */}
        <div className="mt-6 pt-4 border-t border-[#343434] flex flex-col sm:flex-row items-center justify-between gap-3">
          <button
            onClick={onReturnToStudentDashboard}
            className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-[#343434] bg-[#171717] hover:bg-[#202020] text-xs text-[#B7B3B0] hover:text-[#F5F2EF] font-medium transition-colors"
          >
            Return to Learning Portal
          </button>

          <button
            onClick={onViewTeacherDashboard}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center space-x-2"
          >
            <School className="w-4 h-4 text-white" />
            <span>Verify Live on Instructor Dashboard</span>
            <ArrowRight className="w-4 h-4 ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
