import React from 'react';
import { Sparkles, RefreshCw, UserCheck, GraduationCap, School, BookOpen } from 'lucide-react';

interface NavbarProps {
  currentRole: 'teacher' | 'student' | 'advanced';
  onRoleChange: (role: 'teacher' | 'student' | 'advanced') => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onResetDemo: () => void;
  isResetting: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentRole,
  onRoleChange,
  activeTab,
  onTabChange,
  onResetDemo,
  isResetting
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      {/* Top Demo Bar */}
      <div className="bg-slate-900 text-slate-200 px-4 py-1.5 text-xs flex flex-wrap items-center justify-between border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-medium text-slate-300">Live Hackathon Demo Mode:</span>
          <span className="text-slate-400">PostgreSQL 17 Backend Active</span>
        </div>

        <div className="flex items-center space-x-3 mt-1 sm:mt-0">
          <span className="text-slate-400 hidden sm:inline">1-Click Switch Role:</span>
          <div className="flex bg-slate-800 rounded-md p-0.5 border border-slate-700">
            <button
              onClick={() => onRoleChange('teacher')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex items-center space-x-1.5 ${
                currentRole === 'teacher'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <School className="w-3.5 h-3.5" />
              <span>Teacher (Prof. Sen)</span>
            </button>
            <button
              onClick={() => onRoleChange('student')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex items-center space-x-1.5 ${
                currentRole === 'student'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <GraduationCap className="w-3.5 h-3.5" />
              <span>Student (Aarav - Gap: 28%)</span>
            </button>
            <button
              onClick={() => onRoleChange('advanced')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex items-center space-x-1.5 ${
                currentRole === 'advanced'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Advanced (Priya - 92%)</span>
            </button>
          </div>

          <button
            onClick={onResetDemo}
            disabled={isResetting}
            title="Reset database back to 80 calibrated students with 28% Recursion"
            className="flex items-center space-x-1 bg-rose-950/60 border border-rose-700/50 hover:bg-rose-900 text-rose-300 px-2.5 py-1 rounded text-xs font-medium transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${isResetting ? 'animate-spin' : ''}`} />
            <span>{isResetting ? 'Resetting...' : 'Reset Demo'}</span>
          </button>
        </div>
      </div>

      {/* Main Navbar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-4">
            <div 
              onClick={() => onTabChange('dashboard')}
              className="flex items-center space-x-2.5 cursor-pointer group"
            >
              <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm group-hover:bg-indigo-700 transition-colors">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-lg text-slate-900 tracking-tight">AdaptiveClass <span className="text-indigo-600">AI</span></span>
                <span className="hidden md:inline-block ml-2 px-2 py-0.5 text-[11px] font-semibold bg-slate-100 text-slate-600 rounded border border-slate-200">
                  Data Structures • B.E. CSE
                </span>
              </div>
            </div>
          </div>

          {/* Nav links */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {currentRole === 'teacher' ? (
              <>
                <button
                  onClick={() => onTabChange('dashboard')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'dashboard'
                      ? 'text-indigo-600 bg-indigo-50 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  Class Overview
                </button>
                <button
                  onClick={() => onTabChange('students')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'students'
                      ? 'text-indigo-600 bg-indigo-50 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  Student Roster (80)
                </button>
                <button
                  onClick={() => onTabChange('landing')}
                  className="px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
                >
                  Product Story
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => onTabChange('student-dashboard')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'student-dashboard'
                      ? 'text-indigo-600 bg-indigo-50 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  My Progress
                </button>
                <button
                  onClick={() => onTabChange('adaptive-quiz')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                    activeTab === 'adaptive-quiz'
                      ? 'text-indigo-600 bg-indigo-50 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Adaptive Practice</span>
                </button>
                <button
                  onClick={() => onTabChange('landing')}
                  className="px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
                >
                  About
                </button>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};
