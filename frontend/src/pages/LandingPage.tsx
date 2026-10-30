import React from 'react';
import { 
  School, GraduationCap, ArrowRight, ShieldCheck, 
  Sparkles, AlertOctagon, TrendingUp 
} from 'lucide-react';
import { LetterGlitch } from '../components/LetterGlitch';
import { SubjectSummary } from '../types';

interface LandingPageProps {
  onSelectRole: (role: 'teacher' | 'student' | 'advanced') => void;
  onNavigateToTab?: (tab: string, subjectId?: string) => void;
  subjects?: SubjectSummary[];
}

export const LandingPage: React.FC<LandingPageProps> = ({ 
  onSelectRole,
  onNavigateToTab,
  subjects: _subjects = []
}) => {
  return (
    <div className="space-y-16 pb-20">
      {/* 1. HERO SECTION WITH BRIGHTER LETTERGLITCH MATRIX */}
      <section className="relative min-h-[580px] sm:min-h-[640px] flex items-center justify-center overflow-hidden border-b border-[#343434]">
        {/* LetterGlitch Matrix Canvas Background */}
        <div className="absolute inset-0 z-0">
          <LetterGlitch
            glitchSpeed={50}
            centerVignette={true}
            outerVignette={true}
            smooth={true}
          />
        </div>

        {/* Hero Foreground Content */}
        <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center space-y-6">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[#06110C]/90 border border-[#20372B] text-[#B7B3B0] text-xs font-mono shadow-md backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-[#A31C1B] animate-pulse" />
            <span>Autonomous Learning Intelligence • Engineering Classrooms</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[#F5F2EF] tracking-tight leading-tight">
            Every student learns differently.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#F5F2EF] via-[#E24A49] to-[#A31C1B] block sm:inline">
              Your classroom should know it.
            </span>
          </h1>

          <p className="text-base sm:text-lg text-[#B7B3B0] max-w-2xl mx-auto leading-relaxed">
            Continuous concept diagnostics, acute bottleneck isolation, and 1-on-1 Socratic practice connecting live university assessments with explainable classroom intelligence.
          </p>

          {/* Primary Route Buttons */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3.5">
            <button
              onClick={() => onSelectRole('teacher')}
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] active:bg-[#7F1717] text-[#F5F2EF] font-bold text-xs shadow-lg shadow-[#A31C1B]/25 transition-all flex items-center justify-center space-x-2.5"
            >
              <School className="w-4 h-4 text-[#F5F2EF]" />
              <span>Launch Class Overview (Instructor)</span>
              <ArrowRight className="w-4 h-4 ml-0.5" />
            </button>

            <button
              onClick={() => onSelectRole('student')}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-[#202020] hover:bg-[#282828] border border-[#343434] hover:border-[#A31C1B] text-[#F5F2EF] font-semibold text-xs shadow-xs transition-all flex items-center justify-center space-x-2"
            >
              <GraduationCap className="w-4 h-4 text-[#A31C1B]" />
              <span>Enter as Student (Aarav Sharma)</span>
            </button>

            <button
              onClick={() => onSelectRole('advanced')}
              className="text-[#898582] hover:text-[#F5F2EF] text-xs font-medium px-3 py-2 underline transition-colors"
            >
              or view Scholar (Priya)
            </button>
          </div>

          {/* Teacher Agency Philosophy Badge */}
          <div className="pt-2 flex items-center justify-center space-x-2 text-xs text-[#898582] font-mono">
            <ShieldCheck className="w-4 h-4 text-[#A31C1B] flex-shrink-0" />
            <span>Core Principle: <strong className="text-[#B7B3B0]">AI augments the teacher; it does not replace the teacher.</strong></span>
          </div>
        </div>
      </section>

      {/* 2. THREE MEANINGFUL CLASS-WIDE INDICATORS */}
      <section 
        aria-label="Class-wide Empirical Baseline"
        className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8"
      >
        <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 sm:p-7 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 pb-4 mb-4 border-b border-[#343434]">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#A31C1B] block font-semibold">
                Class-wide Analytical Grounding
              </span>
              <h2 className="text-base font-bold text-[#F5F2EF] tracking-tight">
                Department of Computer Science & Engineering • 80 Enrolled Students
              </h2>
            </div>
            <span className="text-xs font-mono text-emerald-400 flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>PostgreSQL 17 Database Active</span>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-[#171717] rounded-xl border border-[#343434]">
              <div className="flex items-center justify-between text-[#898582] text-xs font-mono">
                <span>Active Cohort</span>
                <span className="text-[#A31C1B] font-bold">100%</span>
              </div>
              <span className="text-3xl font-bold font-mono text-[#F5F2EF] mt-1 block tabular-nums">
                80 Students
              </span>
              <span className="text-[11px] text-[#898582] mt-1 block">
                Evaluated continuously across baseline and adaptive practice
              </span>
            </div>

            <div className="p-4 bg-[#171717] rounded-xl border border-[#343434]">
              <div className="flex items-center justify-between text-[#898582] text-xs font-mono">
                <span>Cohort Average</span>
                <TrendingUp className="w-4 h-4 text-[#A31C1B]" />
              </div>
              <span className="text-3xl font-bold font-mono text-[#F5F2EF] mt-1 block tabular-nums">
                59.2%
              </span>
              <span className="text-[11px] text-[#898582] mt-1 block">
                Targeting 70% department mastery benchmark
              </span>
            </div>

            <div className="p-4 bg-[#261214] rounded-xl border border-[#5C1D20]">
              <div className="flex items-center justify-between text-rose-300 text-xs font-mono">
                <span>Acute Concept Bottleneck</span>
                <AlertOctagon className="w-4 h-4 text-rose-400" />
              </div>
              <span className="text-2xl font-bold font-mono text-rose-200 mt-1 block truncate">
                Recursion (35%)
              </span>
              <span className="text-[11px] text-rose-300 mt-1 block">
                23 students requiring call-stack intervention before midterms
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* 3. VISUAL SUBJECT OVERVIEW WITH CLICKABLE SUBJECT PREVIEWS */}
      <section 
        aria-label="Subject Preview Directory"
        className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-[#F5F2EF] tracking-tight">
              Curriculum Core Subjects
            </h2>
            <p className="text-xs text-[#898582]">
              Select a subject to drill down into its topic-level diagnostics and evidence-based reports
            </p>
          </div>

          <button
            onClick={() => onNavigateToTab ? onNavigateToTab('subjects') : onSelectRole('teacher')}
            className="text-xs font-mono text-[#A31C1B] hover:text-[#E24A49] flex items-center space-x-1 transition-colors"
          >
            <span>View All Subjects</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              id: 'cs-201-data-structures',
              code: 'CS-201',
              name: 'Data Structures & Algorithms',
              semester: 'Semester 3',
              average: '59.2%',
              bottleneck: 'Recursion (35%)',
              isLive: true
            },
            {
              id: 'cs-204-database-systems',
              code: 'CS-204',
              name: 'Database Management Systems',
              semester: 'Semester 4',
              average: '63.5%',
              bottleneck: 'Normalization (44%)',
              isLive: false
            },
            {
              id: 'cs-301-operating-systems',
              code: 'CS-301',
              name: 'Operating Systems Principles',
              semester: 'Semester 4',
              average: '61.7%',
              bottleneck: 'Virtual Memory (47%)',
              isLive: false
            },
            {
              id: 'cs-302-computer-networks',
              code: 'CS-302',
              name: 'Computer Networks & Protocols',
              semester: 'Semester 5',
              average: '62.9%',
              bottleneck: 'Subnetting (42%)',
              isLive: false
            }
          ].map((subj) => (
            <div
              key={subj.id}
              onClick={() => {
                if (onNavigateToTab) {
                  onNavigateToTab('subject-report', subj.id);
                } else {
                  onSelectRole('teacher');
                }
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  if (onNavigateToTab) onNavigateToTab('subject-report', subj.id);
                  else onSelectRole('teacher');
                }
              }}
              className="p-5 rounded-2xl bg-[#202020] hover:bg-[#0B1B14] border border-[#343434] hover:border-[#20372B] transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#0B1B14] text-[#F5F2EF] border border-[#20372B]">
                    {subj.code}
                  </span>
                  {subj.isLive && (
                    <span className="text-[10px] font-mono text-emerald-400 flex items-center space-x-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      <span>Live DB</span>
                    </span>
                  )}
                </div>

                <h3 className="text-sm font-bold text-[#F5F2EF] group-hover:text-[#E24A49] transition-colors">
                  {subj.name}
                </h3>
                <span className="text-[11px] text-[#898582] font-mono block mt-0.5">
                  {subj.semester}
                </span>

                <div className="my-4 pt-3 border-t border-[#343434] space-y-1">
                  <div className="flex items-baseline justify-between text-xs font-mono">
                    <span className="text-[#898582]">Average:</span>
                    <span className="font-bold text-[#F5F2EF] tabular-nums">{subj.average}</span>
                  </div>
                  <div className="flex items-baseline justify-between text-xs font-mono">
                    <span className="text-[#898582] text-[11px]">Acute Gap:</span>
                    <span className="text-rose-400 text-[11px] font-medium truncate max-w-[120px]">{subj.bottleneck}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between text-xs font-mono text-[#A31C1B]">
                <span className="text-[11px]">Open Report</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. CONCISE PRIORITY INSIGHT BANNER */}
      <section 
        aria-label="Current Curricular Priority"
        className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8"
      >
        <div className="p-5 rounded-2xl bg-[#202020] border border-[#343434] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className="w-8 h-8 rounded-lg bg-[#0B1B14] border border-[#20372B] flex items-center justify-center text-[#A31C1B] flex-shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#A31C1B] font-semibold block">
                Active Priority Insight
              </span>
              <p className="text-xs sm:text-sm text-[#F5F2EF] mt-0.5 leading-relaxed">
                <strong>23 students in Data Structures</strong> require targeted recursion base-case instruction before mid-term assessments.
              </p>
            </div>
          </div>

          <button
            onClick={() => onNavigateToTab ? onNavigateToTab('insights') : onSelectRole('teacher')}
            className="px-4 py-2 rounded-xl bg-[#171717] hover:bg-[#261214] border border-[#343434] hover:border-[#5C1D20] text-[#F5F2EF] transition-colors flex items-center space-x-1.5 flex-shrink-0 self-start sm:self-auto text-xs font-medium"
          >
            <span>Review Full Action Memo</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </section>
    </div>
  );
};
