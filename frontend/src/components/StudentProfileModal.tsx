import React from 'react';
import { X, Bot, AlertOctagon, CheckCircle2, TrendingDown, BookOpen, User } from 'lucide-react';
import { StudentProfileResponse } from '../types';

interface StudentProfileModalProps {
  profile: StudentProfileResponse | null;
  onClose: () => void;
  onSimulateStudentPractice?: (studentId: number) => void;
}

export const StudentProfileModal: React.FC<StudentProfileModalProps> = ({
  profile,
  onClose,
  onSimulateStudentPractice
}) => {
  if (!profile) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-slate-200 max-w-2xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white text-lg">
              {profile.student_name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white">{profile.student_name}</h3>
                <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
                  {profile.roll_number}
                </span>
              </div>
              <p className="text-xs text-slate-400">{profile.email}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Top Metrics Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
              <span className="text-xs text-slate-500 font-medium">Overall Mastery</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">{profile.overall_mastery}%</p>
              <span className="inline-block mt-1 text-[11px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                {profile.status_label}
              </span>
            </div>

            <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-center">
              <span className="text-xs text-rose-600 font-medium">Critical Learning Gap</span>
              <p className="text-xl font-bold text-rose-700 mt-1 flex items-center justify-center space-x-1">
                <AlertOctagon className="w-4 h-4 text-rose-600" />
                <span>{profile.current_learning_gap}</span>
              </p>
              <span className="text-[11px] text-rose-600 font-medium">Needs Support</span>
            </div>

            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-center col-span-2 sm:col-span-1">
              <span className="text-xs text-emerald-700 font-medium">Strongest Area</span>
              <p className="text-xl font-bold text-emerald-800 mt-1 flex items-center justify-center space-x-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Arrays</span>
              </p>
              <span className="text-[11px] text-emerald-700 font-medium">Mastery Confirmed</span>
            </div>
          </div>

          {/* Concept-by-Concept Breakdown */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Concept Mastery Breakdown</h4>
            <div className="space-y-2.5">
              {profile.concept_performance.map((c) => (
                <div key={c.concept_id} className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2 w-32">
                    <span className="font-medium text-slate-800">{c.concept_name}</span>
                  </div>
                  <div className="flex-1 mx-3">
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          c.status_color === 'green'
                            ? 'bg-emerald-500'
                            : c.status_color === 'blue'
                            ? 'bg-blue-500'
                            : c.status_color === 'amber'
                            ? 'bg-amber-500'
                            : 'bg-rose-500'
                        }`}
                        style={{ width: `${c.mastery}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="w-16 text-right font-semibold text-slate-800">
                    {c.mastery}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Performance Progression */}
          {profile.recent_performance && profile.recent_performance.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center space-x-1">
                <TrendingDown className="w-3.5 h-3.5 text-rose-500" />
                <span>Recent Quiz History (Downwards Trend in Recursion)</span>
              </h4>
              <div className="bg-slate-50 border border-slate-200 rounded-xl divide-y divide-slate-200 text-xs">
                {profile.recent_performance.map((q) => (
                  <div key={q.quiz_id} className="p-2.5 flex items-center justify-between">
                    <div>
                      <span className="font-medium text-slate-800">{q.quiz_title}</span>
                      <span className="text-slate-400 ml-2">{q.timestamp}</span>
                    </div>
                    <div className="font-bold text-slate-900">
                      Score: <span className={q.accuracy < 50 ? 'text-rose-600' : 'text-slate-900'}>{q.accuracy}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Learning Insight & Next Steps */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
            <div className="flex items-center space-x-2 text-indigo-900 font-bold text-xs uppercase tracking-wide mb-2">
              <Bot className="w-4 h-4 text-indigo-600" />
              <span>AI Learning Insight for {profile.student_name}</span>
            </div>
            <p className="text-sm text-indigo-950 mb-3 leading-relaxed">
              {profile.ai_insight}
            </p>

            <div className="border-t border-indigo-200/60 pt-3">
              <span className="text-xs font-semibold text-indigo-900 uppercase tracking-wide">Suggested Next Steps:</span>
              <ul className="mt-1.5 space-y-1 text-xs text-indigo-950 list-disc list-inside">
                {profile.suggested_steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="bg-slate-50 px-6 py-3 border-t border-slate-200 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Student Data ID: #{profile.student_id} • Semester 3
          </span>
          <div className="flex space-x-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
            >
              Close
            </button>
            {onSimulateStudentPractice && (
              <button
                onClick={() => onSimulateStudentPractice(profile.student_id)}
                className="px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition-colors flex items-center space-x-1.5 shadow-sm"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Simulate Student Practice Flow</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
