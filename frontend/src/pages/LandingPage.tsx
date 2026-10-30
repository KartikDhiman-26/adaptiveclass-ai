import React from 'react';
import { School, GraduationCap, UserCheck, ArrowRight, Sparkles, CheckCircle2, ShieldCheck, Target, Zap, BarChart3 } from 'lucide-react';

interface LandingPageProps {
  onSelectRole: (role: 'teacher' | 'student' | 'advanced') => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onSelectRole }) => {
  return (
    <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-slate-50 via-white to-slate-50">
      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 pt-12 pb-16 text-center">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold mb-6 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Autonomous Learning Intelligence for College Classrooms</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight max-w-4xl mx-auto">
          Every Student Learns Differently.{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-600">
            Your Classroom Should Know It.
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          AI-powered learning analytics that helps college professors pinpoint acute concept gaps across 80+ students,
          take targeted instructional action, and deliver personalized adaptive practice.
        </p>

        {/* Philosophy Badge */}
        <div className="mt-5 inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs sm:text-sm font-medium shadow-md">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Core Philosophy: <strong>AI augments the teacher; it does not replace the teacher.</strong></span>
        </div>

        {/* 1-Click Interactive Demo Buttons */}
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <button
            onClick={() => onSelectRole('teacher')}
            className="flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-md hover:shadow-lg transition-all"
          >
            <School className="w-4 h-4" />
            <span>Launch Teacher Dashboard</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>

          <button
            onClick={() => onSelectRole('student')}
            className="flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 font-semibold text-sm shadow-sm hover:shadow transition-all"
          >
            <GraduationCap className="w-4 h-4 text-indigo-600" />
            <span>Student Demo (Aarav - Gap: 28%)</span>
          </button>

          <button
            onClick={() => onSelectRole('advanced')}
            className="flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 font-semibold text-sm transition-all"
          >
            <UserCheck className="w-4 h-4 text-emerald-600" />
            <span>Advanced Learner (Priya - 92%)</span>
          </button>
        </div>
      </section>

      {/* Product Story: Before vs Problem vs After */}
      <section className="max-w-6xl mx-auto px-4 py-12 border-t border-slate-200">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">The Problem We Solve</h2>
          <p className="text-sm text-slate-500 mt-1">From opaque class averages to granular concept mastery</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-600 bg-rose-50 px-2.5 py-1 rounded">
              Traditional Classroom
            </span>
            <h3 className="text-lg font-bold text-slate-900 mt-4">One Average Score</h3>
            <div className="my-4 p-4 bg-slate-50 border border-slate-200 rounded-xl text-center">
              <span className="text-3xl font-black text-slate-700">64%</span>
              <p className="text-xs text-slate-500 mt-1">Class Average Score</p>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              A 64% average tells the professor almost nothing: Who struggles with recursion? Who has mastered trees? Who is ready for advanced algorithms?
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2.5 py-1 rounded">
              The Critical Problem
            </span>
            <h3 className="text-lg font-bold text-slate-900 mt-4">Hidden Learning Gaps</h3>
            <div className="my-4 p-3 bg-amber-50/60 border border-amber-200/80 rounded-xl space-y-1.5 text-xs">
              <div className="flex justify-between font-medium text-slate-800">
                <span>Arrays</span><span className="text-emerald-700 font-bold">82% ✓</span>
              </div>
              <div className="flex justify-between font-medium text-slate-800">
                <span>Trees</span><span className="text-amber-700 font-bold">41% ⚠</span>
              </div>
              <div className="flex justify-between font-medium text-slate-800">
                <span>Recursion</span><span className="text-rose-700 font-bold">35% 🔴 (23 students)</span>
              </div>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Without concept-level breakdown, teachers advance to complex topics while 23 students are fundamentally stuck on recursion base cases.
            </p>
          </div>

          <div className="bg-indigo-950 text-white rounded-2xl border border-indigo-900 p-6 shadow-md">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-300 bg-indigo-900 px-2.5 py-1 rounded border border-indigo-700">
              AdaptiveClass AI
            </span>
            <h3 className="text-lg font-bold text-white mt-4">Targeted Intervention</h3>
            <div className="my-4 p-3 bg-indigo-900/60 border border-indigo-800 rounded-xl space-y-1 text-xs">
              <p className="font-semibold text-emerald-400">✓ Teacher gets actionable revision alerts</p>
              <p className="font-semibold text-indigo-200">✓ Aarav gets beginner recursion practice</p>
              <p className="font-semibold text-amber-300">✓ Advanced learners receive AVL challenges</p>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Same classroom. Different learning paths. The teacher remains in control—AI simply makes the classroom observable.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works: 4-Step Cycle */}
      <section className="max-w-6xl mx-auto px-4 py-12 border-t border-slate-200">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">The Adaptive Learning Loop</h2>
          <p className="text-sm text-slate-500 mt-1">From real quiz data to visible classroom improvement</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 font-bold text-sm flex items-center justify-center mx-auto mb-3">
              1
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Assess</h4>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Students take quizzes across core concepts. Raw answers and attempts are captured in PostgreSQL.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm">
            <div className="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 font-bold text-sm flex items-center justify-center mx-auto mb-3">
              2
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Analyze</h4>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Analytics engine computes individual and classroom concept mastery, isolating critical learning gaps.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm">
            <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 font-bold text-sm flex items-center justify-center mx-auto mb-3">
              3
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Adapt</h4>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Questions adapt in real-time (Beginner ➔ Intermediate ➔ Advanced) based on each student's accuracy.
            </p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm">
            <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 font-bold text-sm flex items-center justify-center mx-auto mb-3">
              4
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Improve</h4>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Student mastery updates dynamically, immediately reducing class support counts on the Teacher Dashboard.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
