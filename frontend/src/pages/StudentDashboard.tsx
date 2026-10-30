import React, { useEffect, useState } from 'react';
import { 
  CheckCircle2, AlertOctagon, AlertTriangle, ArrowRight, 
  Sparkles, Clock, BookOpen, Award, BarChart3, RefreshCw
} from 'lucide-react';
import { StudentProfileResponse, StudentRecommendation } from '../types';
import { api } from '../api';

interface StudentDashboardProps {
  studentId: number;
  onStartQuiz: (conceptId?: number) => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  studentId,
  onStartQuiz
}) => {
  const [profile, setProfile] = useState<StudentProfileResponse | null>(null);
  const [recommendation, setRecommendation] = useState<StudentRecommendation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [studentId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profData, recData] = await Promise.all([
        api.getStudentProfile(studentId),
        api.getStudentRecommendations(studentId)
      ]);
      setProfile(profData);
      setRecommendation(recData);
    } catch (err) {
      console.error("Failed to load student dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !profile) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
        <p className="text-sm text-slate-500 font-medium">Loading personal learning profile...</p>
      </div>
    );
  }

  const strongConcepts = profile.concept_performance.filter(c => c.mastery >= 65);
  const weakConcepts = profile.concept_performance.filter(c => c.mastery < 65);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Student Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
            Student Learning Portal
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mt-1 flex items-center space-x-2">
            <span>Good morning, {profile.student_name.split(' ')[0]}</span>
            <span>👋</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Roll No: {profile.roll_number} • B.E. CSE Data Structures
          </p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <span className="text-xs text-slate-400 font-medium">Your Overall Mastery</span>
            <div className="text-2xl font-black text-slate-900">{profile.overall_mastery}%</div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-sm">
            {profile.overall_mastery >= 85 ? 'A+' : profile.overall_mastery >= 65 ? 'B' : 'C'}
          </div>
        </div>
      </div>

      {/* 2. RECOMMENDED PRACTICE HERO CARD (The Core Differentiator) */}
      {recommendation && (
        <div className="bg-gradient-to-r from-indigo-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-md border border-indigo-800/50">
          <div className="flex items-center space-x-2 text-xs font-bold text-amber-300 uppercase tracking-wider mb-2">
            <Sparkles className="w-4 h-4" />
            <span>Targeted Recommendation For You</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
            <div className="lg:col-span-2">
              <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                {recommendation.recommendation_title}
              </h2>

              <p className="text-sm text-indigo-200 mt-2 leading-relaxed">
                {recommendation.reason}
              </p>

              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <span className="flex items-center space-x-1 bg-indigo-800/60 px-3 py-1 rounded-full border border-indigo-700/50 text-indigo-200">
                  <Clock className="w-3.5 h-3.5" />
                  <span>~{recommendation.estimated_minutes} min estimated practice</span>
                </span>
                <span className="bg-indigo-800/60 px-3 py-1 rounded-full border border-indigo-700/50 text-indigo-200">
                  Difficulty Level: <strong>{recommendation.difficulty_entry}</strong>
                </span>
              </div>

              {/* Topics list */}
              <div className="mt-4 bg-indigo-950/60 border border-indigo-800/60 rounded-xl p-3 text-xs space-y-1 text-slate-300">
                <span className="font-semibold text-white">Recommended Focus Topics:</span>
                {recommendation.topics.map((t, idx) => (
                  <div key={idx} className="flex items-center space-x-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                    <span>{t}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* CTA action */}
            <div className="lg:text-right flex flex-col items-stretch lg:items-end">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 mb-4 border border-white/10 text-left">
                <span className="text-xs text-indigo-200">Current Concept Mastery:</span>
                <div className="text-3xl font-extrabold text-rose-400 mt-1">
                  {recommendation.current_mastery}%
                </div>
                <span className="text-[11px] text-slate-300">Target: Reach ≥65%</span>
              </div>

              <button
                onClick={() => onStartQuiz()}
                className="w-full lg:w-auto px-6 py-3.5 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center space-x-2"
              >
                <BookOpen className="w-4 h-4" />
                <span>Start Adaptive Practice</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. Concept Breakdown: Strong Areas vs Needs Practice */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strong Areas */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-emerald-700 font-bold text-sm mb-4">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>Demonstrated Strong Areas</span>
          </div>

          <div className="space-y-3">
            {strongConcepts.map(c => (
              <div key={c.concept_id} className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-xl flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-slate-900 text-sm">{c.concept_name}</h4>
                  <span className="text-xs text-emerald-700 font-medium">Ready for intermediate/advanced problems</span>
                </div>
                <span className="text-lg font-bold text-emerald-800">{c.mastery}%</span>
              </div>
            ))}
            {strongConcepts.length === 0 && (
              <p className="text-xs text-slate-400 italic">No concepts have reached high mastery yet.</p>
            )}
          </div>
        </div>

        {/* Needs Practice */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-rose-700 font-bold text-sm mb-4">
            <AlertOctagon className="w-5 h-5 text-rose-600" />
            <span>Needs Practice & Reinforcement</span>
          </div>

          <div className="space-y-3">
            {weakConcepts.map(c => (
              <div 
                key={c.concept_id} 
                className={`p-3 rounded-xl border flex items-center justify-between ${
                  c.mastery < 40 
                    ? 'bg-rose-50 border-rose-200' 
                    : 'bg-amber-50 border-amber-200'
                }`}
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-slate-900 text-sm">{c.concept_name}</h4>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      c.mastery < 40 ? 'bg-rose-200 text-rose-800' : 'bg-amber-200 text-amber-800'
                    }`}>
                      {c.mastery < 40 ? 'CRITICAL GAP' : 'DEVELOPING'}
                    </span>
                  </div>
                  <span className="text-xs text-slate-600 mt-0.5 inline-block">
                    {c.concept_name === 'Recursion' 
                      ? 'Base cases and call stack depth require review' 
                      : 'Practice recommended to cement fundamentals'}
                  </span>
                </div>
                <span className={`text-lg font-bold ${c.mastery < 40 ? 'text-rose-700' : 'text-amber-700'}`}>
                  {c.mastery}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
