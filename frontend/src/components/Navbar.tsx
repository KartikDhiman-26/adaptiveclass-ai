import React, { useState, useRef, useEffect } from 'react';
import { 
  Sparkles, RefreshCw, UserCheck, GraduationCap, 
  School, BookOpen, Menu, X, ChevronDown, Check
} from 'lucide-react';
import { ClassStudentItem } from '../types';

interface NavbarProps {
  currentRole: 'teacher' | 'student';
  onRoleChange: (role: 'teacher' | 'student', studentId?: number) => void;
  activeStudent?: ClassStudentItem | null;
  studentsList: ClassStudentItem[];
  activeTab: string;
  onTabChange: (tab: string) => void;
  onResetDemo: () => void;
  isResetting: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentRole,
  onRoleChange,
  activeStudent,
  studentsList,
  activeTab,
  onTabChange,
  onResetDemo,
  isResetting
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false);

  // Sliding indicator state
  const navContainerRef = useRef<HTMLDivElement | null>(null);
  const [indicatorStyle, setIndicatorStyle] = useState<{ left: number; width: number }>({ left: 0, width: 0 });

  const handleNavClick = (tab: string) => {
    onTabChange(tab);
    setIsMobileMenuOpen(false);
  };

  const handleSelectRole = (role: 'teacher' | 'student', studentId?: number) => {
    onRoleChange(role, studentId);
    setIsRoleDropdownOpen(false);
    setIsMobileMenuOpen(false);
  };

  // Update sliding indicator position on tab change and on window resize
  useEffect(() => {
    const updateIndicator = () => {
      if (!navContainerRef.current) return;
      const activeButton = navContainerRef.current.querySelector<HTMLButtonElement>('[data-active="true"]');
      if (activeButton) {
        const containerRect = navContainerRef.current.getBoundingClientRect();
        const buttonRect = activeButton.getBoundingClientRect();
        setIndicatorStyle({
          left: buttonRect.left - containerRect.left,
          width: buttonRect.width
        });
      } else {
        setIndicatorStyle({ left: 0, width: 0 });
      }
    };

    updateIndicator();
    const frameId = requestAnimationFrame(updateIndicator);
    const timer = setTimeout(updateIndicator, 50);

    window.addEventListener('resize', updateIndicator);
    return () => {
      cancelAnimationFrame(frameId);
      clearTimeout(timer);
      window.removeEventListener('resize', updateIndicator);
    };
  }, [activeTab, currentRole]);

  return (
    <header className="bg-[#171717]/95 backdrop-blur-md border-b border-[#343434] sticky top-0 z-40 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* 1. BRAND ANCHOR (Left) */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            <button 
              onClick={() => handleNavClick('landing')}
              aria-label="Go to Overview"
              className="flex items-center space-x-2.5 group text-left"
            >
              <div className="w-8 h-8 rounded-lg bg-[#0B1B14] border border-[#20372B] flex items-center justify-center text-[#A31C1B] shadow-xs group-hover:border-[#A31C1B] transition-colors">
                <Sparkles className="w-4 h-4 text-[#A31C1B]" />
              </div>
              <div>
                <div className="flex items-center space-x-1.5">
                  <span className="font-bold text-base text-[#F5F2EF] tracking-tight">
                    AdaptiveClass
                  </span>
                  <span className="text-[#A31C1B] font-mono font-bold text-sm">
                    AI
                  </span>
                </div>
              </div>
            </button>

            <span className="hidden xl:inline-flex items-center px-2 py-0.5 text-[10px] font-mono text-[#B7B3B0] bg-[#0B1B14] rounded border border-[#20372B]">
              Precision Intelligence
            </span>
          </div>

          {/* 2. PRIMARY NAVIGATION (Center - Single Centered Group) */}
          <div className="hidden md:flex flex-1 justify-center items-center">
            <nav 
              ref={navContainerRef}
              aria-label="Primary Navigation"
              className="relative flex items-center space-x-1 bg-[#06110C]/90 p-1 rounded-xl border border-[#20372B]"
            >
              {/* Sliding Active Pill */}
              {indicatorStyle.width > 0 && (
                <div
                  className="absolute top-1 bottom-1 bg-[#261214] border border-[#5C1D20] rounded-lg transition-all duration-200 ease-out pointer-events-none"
                  style={{
                    left: `${indicatorStyle.left}px`,
                    width: `${indicatorStyle.width}px`
                  }}
                />
              )}

              {/* Navigation Tabs based on Active Persona */}
              {currentRole === 'teacher' ? (
                <>
                  <button
                    data-active={activeTab === 'landing'}
                    onClick={() => handleNavClick('landing')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'landing'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    Overview
                  </button>

                  <button
                    data-active={activeTab === 'dashboard'}
                    onClick={() => handleNavClick('dashboard')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'dashboard'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    Class Overview
                  </button>

                  <button
                    data-active={activeTab === 'subjects' || activeTab === 'subject-report'}
                    onClick={() => handleNavClick('subjects')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'subjects' || activeTab === 'subject-report'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    Subjects
                  </button>

                  <button
                    data-active={activeTab === 'students'}
                    onClick={() => handleNavClick('students')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'students'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    Students
                  </button>

                  <button
                    data-active={activeTab === 'insights'}
                    onClick={() => handleNavClick('insights')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'insights'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    Insights
                  </button>
                </>
              ) : (
                <>
                  <button
                    data-active={activeTab === 'landing'}
                    onClick={() => handleNavClick('landing')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'landing'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    Overview
                  </button>

                  <button
                    data-active={activeTab === 'student-dashboard'}
                    onClick={() => handleNavClick('student-dashboard')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'student-dashboard'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    My Learning Portal
                  </button>

                  <button
                    data-active={activeTab === 'ai-tutor'}
                    onClick={() => handleNavClick('ai-tutor')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'ai-tutor'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#A31C1B]" />
                    <span>AI Tutor Workspace</span>
                  </button>

                  <button
                    data-active={activeTab === 'adaptive-quiz'}
                    onClick={() => handleNavClick('adaptive-quiz')}
                    className={`relative z-10 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5 ${
                      activeTab === 'adaptive-quiz'
                        ? 'text-[#F5F2EF] font-bold'
                        : 'text-[#898582] hover:text-[#F5F2EF]'
                    }`}
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Adaptive Practice</span>
                  </button>
                </>
              )}
            </nav>
          </div>

          {/* 3. EVALUATOR PERSONA DROPDOWN & DEMO RESET (Right) */}
          <div className="hidden sm:flex items-center space-x-2 flex-shrink-0">
            {/* Persona Switcher Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsRoleDropdownOpen(!isRoleDropdownOpen)}
                aria-expanded={isRoleDropdownOpen}
                aria-haspopup="true"
                className="flex items-center space-x-2 px-3 py-1.5 rounded-xl border border-[#343434] bg-[#202020] hover:bg-[#262626] hover:border-[#A31C1B] text-[#F5F2EF] text-xs font-medium transition-colors shadow-xs"
              >
                {currentRole === 'teacher' ? (
                  <>
                    <School className="w-3.5 h-3.5 text-[#A31C1B]" />
                    <span className="font-semibold">Instructor View</span>
                  </>
                ) : (
                  <>
                    <GraduationCap className="w-3.5 h-3.5 text-[#A31C1B]" />
                    <span className="font-semibold truncate max-w-[120px]">
                      {activeStudent ? activeStudent.name : 'Student Mode'}
                    </span>
                    {activeStudent && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#0B1B14] text-emerald-400 border border-[#20372B]">
                        {activeStudent.overall_mastery}%
                      </span>
                    )}
                  </>
                )}
                <ChevronDown className="w-3 h-3 text-[#898582]" />
              </button>

              {/* Dropdown Menu */}
              {isRoleDropdownOpen && (
                <div 
                  className="absolute right-0 mt-1.5 w-72 rounded-xl bg-[#202020] border border-[#343434] shadow-2xl p-2 z-50 text-xs animate-in fade-in duration-100"
                  role="menu"
                >
                  <div className="px-2.5 py-1.5 text-[10px] uppercase font-mono tracking-wider text-[#898582] border-b border-[#343434] mb-1.5 flex items-center justify-between">
                    <span>Select Persona</span>
                    <span className="text-[#A31C1B] font-bold">{studentsList.length} in cohort</span>
                  </div>

                  {/* Teacher Option */}
                  <button
                    onClick={() => handleSelectRole('teacher')}
                    role="menuitem"
                    className={`w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between transition-colors mb-1.5 ${
                      currentRole === 'teacher'
                        ? 'bg-[#261214] border border-[#5C1D20] text-[#F5F2EF] font-semibold'
                        : 'hover:bg-[#282828] text-[#B7B3B0]'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <div className="w-6 h-6 rounded bg-[#0B1B14] border border-[#20372B] flex items-center justify-center">
                        <School className="w-3.5 h-3.5 text-[#A31C1B]" />
                      </div>
                      <div>
                        <div className="font-medium text-[#F5F2EF]">Prof. Vikram Sen</div>
                        <div className="text-[10px] text-[#898582] font-mono">Instructor Diagnostics</div>
                      </div>
                    </div>
                    {currentRole === 'teacher' && <Check className="w-3.5 h-3.5 text-[#A31C1B]" />}
                  </button>

                  {/* Cohort Students Header */}
                  <div className="px-2.5 py-1 text-[10px] uppercase font-mono tracking-wider text-[#898582] border-t border-[#343434] pt-2 mb-1">
                    Cohort Learners ({studentsList.length})
                  </div>

                  {studentsList.length === 0 ? (
                    <div className="px-2.5 py-3 text-center text-[#898582] text-[11px] font-mono">
                      No students enrolled in this cohort
                    </div>
                  ) : (
                    <div className="max-h-60 overflow-y-auto space-y-1 pr-1">
                      {studentsList.map((s) => {
                        const isSelected = currentRole === 'student' && activeStudent?.id === s.id;
                        const isNeedsHelp = s.overall_mastery < 45;
                        const isAdvanced = s.overall_mastery >= 85;

                        return (
                          <button
                            key={s.id}
                            onClick={() => handleSelectRole('student', s.id)}
                            role="menuitem"
                            className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center justify-between transition-colors ${
                              isSelected
                                ? 'bg-[#261214] border border-[#5C1D20] text-[#F5F2EF] font-semibold'
                                : 'hover:bg-[#282828] text-[#B7B3B0]'
                            }`}
                          >
                            <div className="flex items-center space-x-2 min-w-0 pr-2">
                              <div className="w-5 h-5 rounded bg-[#171717] border border-[#343434] flex items-center justify-center flex-shrink-0">
                                {isAdvanced ? (
                                  <UserCheck className="w-3 h-3 text-emerald-400" />
                                ) : (
                                  <GraduationCap className={`w-3 h-3 ${isNeedsHelp ? 'text-rose-400' : 'text-[#898582]'}`} />
                                )}
                              </div>
                              <div className="truncate">
                                <div className="font-medium text-[#F5F2EF] truncate text-xs">{s.name}</div>
                                <div className="text-[10px] text-[#898582] font-mono flex items-center space-x-1">
                                  <span>Roll {s.roll_number}</span>
                                  <span>•</span>
                                  <span className={isNeedsHelp ? 'text-rose-400 font-semibold' : isAdvanced ? 'text-emerald-400 font-semibold' : 'text-[#B7B3B0]'}>
                                    {s.overall_mastery}%
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center space-x-1.5 flex-shrink-0">
                              <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                                isNeedsHelp
                                  ? 'bg-rose-950/40 text-rose-300 border-rose-800/60'
                                  : isAdvanced
                                  ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
                                  : 'bg-[#0B1B14] text-[#B7B3B0] border-[#20372B]'
                              }`}>
                                {s.status_label || (isNeedsHelp ? 'Needs Help' : isAdvanced ? 'Advanced' : 'On Track')}
                              </span>
                              {isSelected && <Check className="w-3.5 h-3.5 text-[#A31C1B]" />}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Subtle Reset Action */}
            <button
              onClick={onResetDemo}
              disabled={isResetting}
              title="Reset PostgreSQL database back to calibrated 80-student baseline"
              className="px-2.5 py-1.5 rounded-xl border border-[#343434] bg-[#202020] text-[#B7B3B0] hover:text-[#F5F2EF] hover:bg-[#282828] hover:border-[#A31C1B] text-xs font-medium transition-colors flex items-center space-x-1.5 disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 text-[#898582] ${isResetting ? 'animate-spin' : ''}`} />
              <span className="hidden lg:inline">{isResetting ? 'Resetting...' : 'Reset'}</span>
            </button>
          </div>

          {/* 4. MOBILE HAMBURGER BUTTON */}
          <div className="flex md:hidden items-center space-x-2">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle mobile navigation menu"
              className="p-2 rounded-lg border border-[#343434] text-[#B7B3B0] hover:bg-[#202020] transition-colors"
            >
              {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* 5. RESPONSIVE MOBILE DRAWER */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-[#343434] bg-[#171717] px-4 py-4 space-y-4 shadow-xl animate-in slide-in-from-top-2 duration-150">
          <div className="space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#898582] block px-2 mb-1">
              Navigation
            </span>
            {currentRole === 'teacher' ? (
              <>
                <button
                  onClick={() => handleNavClick('landing')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold ${
                    activeTab === 'landing' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  Overview
                </button>
                <button
                  onClick={() => handleNavClick('dashboard')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold ${
                    activeTab === 'dashboard' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  Class Overview
                </button>
                <button
                  onClick={() => handleNavClick('subjects')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold ${
                    activeTab === 'subjects' || activeTab === 'subject-report' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  Subjects
                </button>
                <button
                  onClick={() => handleNavClick('students')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold ${
                    activeTab === 'students' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  Students
                </button>
                <button
                  onClick={() => handleNavClick('insights')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold ${
                    activeTab === 'insights' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  Insights
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => handleNavClick('landing')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold ${
                    activeTab === 'landing' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  Overview
                </button>
                <button
                  onClick={() => handleNavClick('student-dashboard')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold ${
                    activeTab === 'student-dashboard' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  My Learning Portal
                </button>
                <button
                  onClick={() => handleNavClick('ai-tutor')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 ${
                    activeTab === 'ai-tutor' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#A31C1B]" />
                  <span>AI Tutor Workspace</span>
                </button>
                <button
                  onClick={() => handleNavClick('adaptive-quiz')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 ${
                    activeTab === 'adaptive-quiz' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Adaptive Practice</span>
                </button>
              </>
            )}
          </div>

          {/* Mobile Persona Switcher */}
          <div className="pt-3 border-t border-[#343434] space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#898582] block px-2">
              Switch Evaluator Persona
            </span>
            <div className="grid grid-cols-1 gap-1.5 max-h-48 overflow-y-auto pr-1">
              <button
                onClick={() => handleSelectRole('teacher')}
                className={`w-full text-left p-2.5 rounded-lg flex items-center justify-between text-xs transition-colors ${
                  currentRole === 'teacher'
                    ? 'bg-[#261214] border border-[#5C1D20] text-[#F5F2EF] font-semibold'
                    : 'bg-[#202020] border border-[#343434] text-[#B7B3B0]'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <School className={`w-3.5 h-3.5 ${currentRole === 'teacher' ? 'text-[#A31C1B]' : 'text-[#898582]'}`} />
                  <span>Prof. Vikram Sen (Instructor)</span>
                </div>
                {currentRole === 'teacher' && <Check className="w-3.5 h-3.5 text-[#A31C1B]" />}
              </button>

              {studentsList.slice(0, 15).map((s) => {
                const isSelected = currentRole === 'student' && activeStudent?.id === s.id;
                return (
                  <button
                    key={s.id}
                    onClick={() => handleSelectRole('student', s.id)}
                    className={`w-full text-left p-2.5 rounded-lg flex items-center justify-between text-xs transition-colors ${
                      isSelected
                        ? 'bg-[#261214] border border-[#5C1D20] text-[#F5F2EF] font-semibold'
                        : 'bg-[#202020] border border-[#343434] text-[#B7B3B0]'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <GraduationCap className={`w-3.5 h-3.5 ${isSelected ? 'text-[#A31C1B]' : 'text-[#898582]'}`} />
                      <span>{s.name} ({s.overall_mastery}%)</span>
                    </div>
                    {isSelected && <Check className="w-3.5 h-3.5 text-[#A31C1B]" />}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => {
                onResetDemo();
                setIsMobileMenuOpen(false);
              }}
              disabled={isResetting}
              className="w-full mt-2 py-2 px-3 rounded-lg border border-[#5C1D20] bg-[#261214] text-rose-300 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
              <span>{isResetting ? 'Resetting Database...' : 'Reset Calibrated Demo Data'}</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
