import React from 'react';
import { X, Sparkles, AlertOctagon, CheckCircle2, GraduationCap } from 'lucide-react';
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
    <div 
      className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150"
      role="dialog"
      aria-modal="true"
      aria-labelledby="student-modal-title"
    >
      <div className="bg-[#202020] rounded-2xl border border-[#343434] max-w-2xl w-full shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="bg-[#171717] px-6 py-4.5 flex items-center justify-between border-b border-[#343434]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#0B1B14] border border-[#20372B] flex items-center justify-center font-bold text-[#C12A29] text-base">
              {profile.student_name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 id="student-modal-title" className="text-base font-bold text-[#F5F2EF]">
                  {profile.student_name}
                </h3>
                <span className="text-xs font-mono bg-[#202020] text-[#B7B3B0] px-2 py-0.5 rounded border border-[#343434]">
                  {profile.roll_number}
                </span>
              </div>
              <p className="text-xs text-[#898582] font-mono mt-0.5">{profile.email}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="text-[#898582] hover:text-[#F5F2EF] p-1.5 rounded-lg hover:bg-[#202020] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[78vh] overflow-y-auto">
          {/* Top Metrics Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-[#171717] border border-[#343434] rounded-xl p-3.5 text-center">
              <span className="text-[11px] uppercase tracking-wider text-[#898582] font-mono font-semibold block">
                Overall Mastery
              </span>
              <p className="text-2xl font-bold font-mono text-[#F5F2EF] mt-1 tabular-nums">
                {profile.overall_mastery}%
              </p>
              <span className="inline-block mt-1 text-[11px] font-mono font-medium text-[#B7B3B0] bg-[#202020] border border-[#343434] px-2 py-0.5 rounded">
                {profile.status_label}
              </span>
            </div>

            <div className="bg-[#261214] border border-[#5C1D20] rounded-xl p-3.5 text-center">
              <span className="text-[11px] uppercase tracking-wider text-rose-300 font-mono font-semibold block">
                Primary Gap
              </span>
              <p className="text-lg font-bold font-mono text-rose-200 mt-1 flex items-center justify-center space-x-1 truncate">
                <AlertOctagon className="w-4 h-4 text-[#C12A29] flex-shrink-0" />
                <span className="truncate">{profile.current_learning_gap}</span>
              </p>
              <span className="text-[11px] text-[#C12A29] font-mono font-medium">Needs Support</span>
            </div>

            <div className="bg-[#0B1B14] border border-[#20372B] rounded-xl p-3.5 text-center col-span-2 sm:col-span-1">
              <span className="text-[11px] uppercase tracking-wider text-emerald-300 font-mono font-semibold block">
                Strongest Concept
              </span>
              <p className="text-lg font-bold font-mono text-emerald-200 mt-1 flex items-center justify-center space-x-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Arrays</span>
              </p>
              <span className="text-[11px] text-emerald-400 font-mono font-medium">Verified Solid</span>
            </div>
          </div>

          {/* Concept-by-Concept Breakdown */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#898582] font-mono mb-3">
              Measured Curricular Competencies
            </h4>
            <div className="space-y-2.5 bg-[#171717] p-4 rounded-xl border border-[#343434]">
              {profile.concept_performance.map((c) => {
                const isCritical = c.mastery < 40;
                const isStrong = c.mastery >= 75;

                return (
                  <div key={c.concept_id} className="flex items-center justify-between text-xs sm:text-sm">
                    <span className="font-medium text-[#F5F2EF] w-32 truncate">
                      {c.concept_name}
                    </span>
                    <div className="flex-1 mx-3 bg-[#06110C] rounded-full h-2 overflow-hidden border border-[#343434]">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          isCritical
                            ? 'bg-[#A31C1B]'
                            : isStrong
                            ? 'bg-emerald-400'
                            : 'bg-emerald-600'
                        }`}
                        style={{ width: `${c.mastery}%` }}
                      />
                    </div>
                    <span className="font-mono text-xs font-bold text-[#F5F2EF] w-12 text-right tabular-nums">
                      {c.mastery}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* AI Pedagogical Insight for this student */}
          <div className="p-4 bg-[#0B1B14] rounded-xl border border-[#20372B] space-y-2">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-[#C12A29]" />
              <span className="text-xs font-mono font-semibold text-[#C12A29] uppercase tracking-wider">
                Prescriptive AI Assessment
              </span>
            </div>
            <p className="text-xs text-[#B7B3B0] leading-relaxed">
              {profile.ai_insight}
            </p>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="bg-[#171717] px-6 py-4 flex items-center justify-between border-t border-[#343434]">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-[#343434] text-[#B7B3B0] hover:text-[#F5F2EF] hover:bg-[#202020] text-xs font-medium transition-colors"
          >
            Close
          </button>

          {onSimulateStudentPractice && (
            <button
              onClick={() => {
                onClose();
                onSimulateStudentPractice(profile.student_id);
              }}
              className="px-4 py-2 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] text-white font-semibold text-xs transition-colors flex items-center space-x-2"
            >
              <GraduationCap className="w-4 h-4" />
              <span>Simulate Adaptive Practice</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
