import React, { useEffect, useState } from 'react';
import { 
  CheckCircle2, AlertOctagon, ArrowRight, 
  Sparkles, Clock, BookOpen, MessageSquare, 
  TrendingDown
} from 'lucide-react';
import { StudentProfileResponse, StudentRecommendation } from '../types';
import { api } from '../api';

interface StudentDashboardProps {
  studentId: number;
  onStartQuiz: (conceptId?: number) => void;
  onOpenTutor?: (conceptId?: number) => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  studentId,
  onStartQuiz,
  onOpenTutor
}) => {
  const [profile, setProfile] = useState<StudentProfileResponse | null>(null);
  const [recommendation, setRecommendation] = useState<StudentRecommendation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    Promise.all([
      api.getStudentProfile(studentId),
      api.getStudentRecommendations(studentId)
    ])
      .then(([profData, recData]) => {
        if (!isMounted) return;
        setProfile(profData);
        setRecommendation(recData);
      })
      .catch((err) => {
        console.error("Failed to load student dashboard:", err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [studentId]);

  if (loading || !profile) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-6 animate-pulse">
        <div className="bg-[#202020] rounded-2xl border border-[#343434] p-8 h-36" />
        <div className="bg-[#202020] rounded-2xl border border-[#343434] p-8 h-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 h-64" />
          <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 h-64" />
        </div>
      </div>
    );
  }

  const strongConcepts = profile.concept_performance.filter(c => c.mastery >= 65);
  const weakConcepts = profile.concept_performance.filter(c => c.mastery < 65);
  const weakestConceptObj = profile.concept_performance.find(c => c.concept_name === profile.current_learning_gap);
  const weakestConceptId = weakestConceptObj ? weakestConceptObj.concept_id : undefined;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. STUDENT MASTHEAD */}
      <header className="bg-[#202020] rounded-2xl border border-[#343434] p-6 sm:p-7 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-semibold uppercase tracking-widest text-[#C12A29] font-mono">
              Academic Term • Semester 3
            </span>
            <span className="text-[#898582]">•</span>
            <span className="text-[11px] text-[#B7B3B0] font-mono">Roll {profile.roll_number}</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-[#F5F2EF] tracking-tight mt-1.5 flex items-center space-x-2">
            <span>Good morning, {profile.student_name.split(' ')[0]}</span>
          </h1>

          <p className="text-xs sm:text-sm text-[#B7B3B0] mt-1 flex flex-wrap items-center gap-x-2">
            <span>Course: <strong className="text-[#F5F2EF] font-semibold">B.E. CSE — Data Structures</strong></span>
            <span className="text-[#898582] hidden sm:inline">•</span>
            <span>Status: <strong className="text-[#F5F2EF] font-semibold">{profile.status_label}</strong></span>
          </p>
        </div>

        {/* Overall Mastery Tile */}
        <div className="flex items-center space-x-4 bg-[#171717] border border-[#343434] p-3.5 rounded-xl self-start sm:self-auto">
          <div className="text-right">
            <span className="text-[11px] uppercase tracking-wider text-[#898582] font-semibold font-mono block">
              Cumulative Mastery
            </span>
            <div className="text-2xl font-bold font-mono text-[#F5F2EF] tabular-nums">
              {profile.overall_mastery}%
            </div>
          </div>
          <div className="w-11 h-11 rounded-lg bg-[#0B1B14] border border-[#20372B] text-emerald-400 flex items-center justify-center font-bold text-base shadow-sm font-mono">
            {profile.overall_mastery >= 85 ? 'A' : profile.overall_mastery >= 65 ? 'B' : 'C'}
          </div>
        </div>
      </header>

      {/* 2. TARGETED REVISION RECOMMENDATION HERO CARD */}
      {recommendation && (
        <section 
          aria-label="Targeted Practice Recommendation"
          className="bg-[#202020] rounded-2xl border border-[#343434] p-6 sm:p-7 shadow-sm relative overflow-hidden"
        >
          <div className="flex flex-wrap items-center justify-between gap-2 mb-4 pb-3 border-b border-[#343434]">
            <div className="flex items-center space-x-2 text-xs font-semibold text-rose-300 bg-[#261214] border border-[#5C1D20] px-2.5 py-0.5 rounded font-mono">
              <AlertOctagon className="w-3.5 h-3.5 text-[#C12A29]" />
              <span>Priority Learning Target: {recommendation.weak_concept}</span>
            </div>

            <div className="flex items-center space-x-2 text-xs text-[#898582] font-mono">
              <Clock className="w-3.5 h-3.5 text-[#898582]" />
              <span>~{recommendation.estimated_minutes} min estimated session</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
            <div className="lg:col-span-2 space-y-3">
              <h2 className="text-xl sm:text-2xl font-bold text-[#F5F2EF] tracking-tight">
                {recommendation.recommendation_title}
              </h2>

              <p className="text-sm text-[#B7B3B0] leading-relaxed">
                {recommendation.reason}
              </p>

              {/* Focus modules */}
              <div className="bg-[#171717] border border-[#343434] rounded-xl p-3.5 text-xs text-[#B7B3B0] space-y-1.5 font-mono">
                <span className="font-semibold text-[#F5F2EF] block text-[11px] uppercase tracking-wider text-[#C12A29]">
                  Recommended Revision Modules:
                </span>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-[11px]">
                  {recommendation.topics.map((t, idx) => (
                    <li key={idx} className="flex items-center space-x-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#A31C1B] flex-shrink-0" />
                      <span className="line-clamp-1">{t}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Action Pod */}
            <div className="bg-[#171717] border border-[#343434] rounded-xl p-5 flex flex-col justify-between space-y-4">
              <div>
                <span className="text-[11px] uppercase tracking-wider text-[#898582] font-semibold font-mono block">
                  Current Mastery Status:
                </span>
                <div className="flex items-baseline space-x-2 mt-1">
                  <span className="text-3xl font-extrabold font-mono text-[#C12A29] tabular-nums">
                    {recommendation.current_mastery}%
                  </span>
                  <span className="text-xs text-[#898582] font-mono">Target: ≥65%</span>
                </div>
                <div className="w-full bg-[#06110C] rounded-full h-1.5 mt-2 overflow-hidden border border-[#343434]">
                  <div
                    className="h-full bg-[#A31C1B] rounded-full"
                    style={{ width: `${recommendation.current_mastery}%` }}
                  />
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-[#343434]">
                <button
                  onClick={() => onStartQuiz(weakestConceptId)}
                  className="w-full px-4 py-2.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center space-x-2"
                >
                  <BookOpen className="w-4 h-4 text-white" />
                  <span>Start Adaptive Practice</span>
                  <ArrowRight className="w-4 h-4 ml-0.5" />
                </button>

                {onOpenTutor && (
                  <button
                    onClick={() => onOpenTutor(weakestConceptId)}
                    className="w-full px-4 py-2 rounded-xl border border-[#343434] bg-[#202020] hover:bg-[#282828] text-[#F5F2EF] font-medium text-xs transition-colors flex items-center justify-center space-x-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#C12A29]" />
                    <span>Explain in AI Tutor Workspace</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* 3. AI TUTOR STUDY COMPANION INVITATION CARD */}
      <section 
        aria-label="AI Tutor Study Companion"
        className="bg-[#0B1B14] rounded-2xl border border-[#20372B] p-6 sm:p-7 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-5"
      >
        <div className="max-w-2xl space-y-1.5">
          <div className="flex items-center space-x-2 text-[#C12A29] font-semibold text-xs tracking-wider uppercase font-mono">
            <Sparkles className="w-4 h-4 text-[#C12A29]" />
            <span>1-on-1 Socratic Learning Tutor</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold text-[#F5F2EF] tracking-tight">
            Need an intuitive mental model or step-by-step trace?
          </h3>
          <p className="text-xs text-[#B7B3B0] leading-relaxed">
            Ask our Socratic tutor to explain base cases like you're five, walk through stack execution frames, or quiz your intuition before taking an exam.
          </p>

          <div className="flex flex-wrap gap-2 pt-2">
            {[
              "Teach me Recursion like I'm 5",
              "Walk me through call stack frames step by step",
              "Where are linked lists used in real software?",
              "Quiz my intuition on tree traversals"
            ].map((prompt, i) => (
              <button
                key={i}
                onClick={() => onOpenTutor && onOpenTutor(weakestConceptId)}
                className="text-[11px] font-mono bg-[#171717] hover:bg-[#202020] text-[#B7B3B0] hover:text-[#F5F2EF] px-3 py-1 rounded-full border border-[#343434] transition-colors"
              >
                → {prompt}
              </button>
            ))}
          </div>
        </div>

        {onOpenTutor && (
          <button
            onClick={() => onOpenTutor(weakestConceptId)}
            className="px-5 py-3 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] border border-[#7F1717] text-white font-semibold text-xs shadow-sm transition-all flex items-center justify-center space-x-2 flex-shrink-0"
          >
            <MessageSquare className="w-4 h-4 text-white" />
            <span>Open AI Tutor Workspace</span>
            <ArrowRight className="w-4 h-4 ml-0.5" />
          </button>
        )}
      </section>

      {/* 4. CURRICULAR CONCEPT PERFORMANCE BREAKDOWN */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Areas Needing Practice & Reinforcement */}
        <section 
          aria-labelledby="weak-concepts-heading"
          className="bg-[#202020] rounded-2xl border border-[#343434] p-6 shadow-sm flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-[#343434]">
              <div className="flex items-center space-x-2 text-[#F5F2EF] font-bold text-sm">
                <AlertOctagon className="w-4 h-4 text-[#C12A29]" />
                <h3 id="weak-concepts-heading">Priority Practice Areas</h3>
              </div>
              <span className="text-[11px] text-[#898582] font-mono">Threshold: &lt;65%</span>
            </div>

            <div className="space-y-3">
              {weakConcepts.map((c) => (
                <div 
                  key={c.concept_id}
                  className="p-3.5 rounded-xl border border-[#343434] bg-[#171717] flex flex-col justify-between space-y-2.5"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-semibold text-[#F5F2EF] text-sm">{c.concept_name}</h4>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border font-mono ${
                          c.mastery < 40 
                            ? 'bg-[#261214] text-rose-300 border-[#5C1D20]' 
                            : 'bg-amber-950/60 text-amber-300 border-amber-800'
                        }`}>
                          {c.mastery < 40 ? 'CRITICAL GAP' : 'DEVELOPING'}
                        </span>
                      </div>
                      <span className="text-xs text-[#898582] mt-0.5 block">
                        {c.concept_name === 'Recursion'
                          ? 'Focus on base case conditions and call stack depth.'
                          : 'Targeted practice recommended to cement invariants.'}
                      </span>
                    </div>

                    <span className="text-xl font-bold font-mono text-[#F5F2EF] tabular-nums">
                      {c.mastery}%
                    </span>
                  </div>

                  {/* Actions for this concept */}
                  <div className="flex items-center justify-end space-x-2 pt-2 border-t border-[#343434]">
                    {onOpenTutor && (
                      <button
                        onClick={() => onOpenTutor(c.concept_id)}
                        className="px-2.5 py-1 text-[11px] font-medium text-[#B7B3B0] hover:text-[#F5F2EF] bg-[#202020] border border-[#343434] rounded-md transition-colors"
                      >
                        Explain Concept
                      </button>
                    )}
                    <button
                      onClick={() => onStartQuiz(c.concept_id)}
                      className="px-3 py-1 text-[11px] font-semibold text-white bg-[#A31C1B] hover:bg-[#C12A29] rounded-md transition-colors flex items-center space-x-1"
                    >
                      <BookOpen className="w-3 h-3" />
                      <span>Practice</span>
                    </button>
                  </div>
                </div>
              ))}

              {weakConcepts.length === 0 && (
                <div className="text-center py-8 text-[#898582] text-xs">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto mb-1.5" />
                  <p className="font-semibold text-[#F5F2EF]">All competencies above baseline</p>
                  <p className="text-[11px]">You have maintained solid proficiency across all active course modules.</p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Demonstrated Strong Areas */}
        <section 
          aria-labelledby="strong-concepts-heading"
          className="bg-[#202020] rounded-2xl border border-[#343434] p-6 shadow-sm flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-[#343434]">
              <div className="flex items-center space-x-2 text-[#F5F2EF] font-bold text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h3 id="strong-concepts-heading">Demonstrated Proficiencies</h3>
              </div>
              <span className="text-[11px] text-[#898582] font-mono">Mastery: ≥65%</span>
            </div>

            <div className="space-y-3">
              {strongConcepts.map((c) => (
                <div 
                  key={c.concept_id}
                  className="p-3.5 rounded-xl border border-[#343434] bg-[#171717] flex items-center justify-between"
                >
                  <div>
                    <h4 className="font-semibold text-[#F5F2EF] text-sm">{c.concept_name}</h4>
                    <span className="text-xs text-[#898582] mt-0.5 block">
                      Competency verified. Ready for advanced challenge problems.
                    </span>
                  </div>

                  <div className="text-right">
                    <span className="text-xl font-bold font-mono text-emerald-400 tabular-nums">
                      {c.mastery}%
                    </span>
                    <button
                      onClick={() => onStartQuiz(c.concept_id)}
                      className="block text-[11px] font-mono text-[#C12A29] hover:text-[#F5F2EF] font-medium underline mt-0.5"
                    >
                      Reinforce
                    </button>
                  </div>
                </div>
              ))}

              {strongConcepts.length === 0 && (
                <p className="text-xs text-[#898582] italic py-8 text-center font-mono">
                  No concepts have reached high mastery yet. Keep practicing!
                </p>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* 5. HISTORICAL ASSESSMENT TRAJECTORY */}
      {profile.recent_performance && profile.recent_performance.length > 0 && (
        <section 
          aria-labelledby="history-heading"
          className="bg-[#202020] rounded-2xl border border-[#343434] p-6 sm:p-7 shadow-sm space-y-4"
        >
          <div className="flex items-center justify-between pb-2 border-b border-[#343434]">
            <div>
              <h3 id="history-heading" className="text-base font-bold text-[#F5F2EF] tracking-tight">
                Assessment History & Diagnostic Trend
              </h3>
              <p className="text-xs text-[#B7B3B0] mt-0.5">
                Past quiz sessions recording concept accuracy in PostgreSQL
              </p>
            </div>
            <div className="flex items-center space-x-1.5 text-xs text-[#898582] font-mono">
              <TrendingDown className="w-3.5 h-3.5 text-[#C12A29]" />
              <span>Downwards trend in Recursion noted</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {profile.recent_performance.map((q) => (
              <div 
                key={q.quiz_id} 
                className="p-4 rounded-xl border border-[#343434] bg-[#171717] flex flex-col justify-between space-y-2"
              >
                <div>
                  <span className="text-[10px] text-[#898582] font-mono uppercase tracking-wider block">
                    {q.timestamp}
                  </span>
                  <h4 className="text-xs font-semibold text-[#F5F2EF] mt-1 line-clamp-1">
                    {q.quiz_title}
                  </h4>
                </div>

                <div className="flex items-baseline justify-between pt-2 border-t border-[#343434]">
                  <span className="text-[11px] text-[#898582] font-mono">Accuracy Score:</span>
                  <span className={`text-base font-bold font-mono tabular-nums ${
                    q.accuracy < 50 ? 'text-[#C12A29]' : 'text-[#F5F2EF]'
                  }`}>
                    {q.accuracy}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
