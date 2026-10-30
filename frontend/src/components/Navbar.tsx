import React, { useState, useRef, useEffect } from 'react';
import { 
  Sparkles, RefreshCw, UserCheck, GraduationCap, 
  School, BookOpen, Menu, X, ChevronDown, Check
} from 'lucide-react';

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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false);

  // Sliding indicator state
  const navContainerRef = useRef<HTMLDivElement | null>(null);
  const [indicatorStyle, setIndicatorStyle] = useState<{ left: number; width: number }>({ left: 0, width: 0 });

  const roleLabels = {
    teacher: { name: 'Prof. Vikram Sen', title: 'Instructor', icon: School },
    student: { name: 'Aarav Sharma', title: 'Student (28% Gap)', icon: GraduationCap },
    advanced: { name: 'Priya Patel', title: 'Advanced (92%)', icon: UserCheck }
  };

  const ActiveRoleIcon = roleLabels[currentRole].icon;

  const handleNavClick = (tab: string) => {
    onTabChange(tab);
    setIsMobileMenuOpen(false);
  };

  const handleRoleSelect = (role: 'teacher' | 'student' | 'advanced') => {
    onRoleChange(role);
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
                <ActiveRoleIcon className="w-3.5 h-3.5 text-[#A31C1B]" />
                <span className="font-semibold">{roleLabels[currentRole].title}</span>
                <ChevronDown className="w-3 h-3 text-[#898582]" />
              </button>

              {/* Dropdown Menu */}
              {isRoleDropdownOpen && (
                <div 
                  className="absolute right-0 mt-1.5 w-60 rounded-xl bg-[#202020] border border-[#343434] shadow-2xl p-1.5 z-50 text-xs animate-in fade-in duration-100"
                  role="menu"
                >
                  <div className="px-2.5 py-1.5 text-[10px] uppercase font-mono tracking-wider text-[#898582] border-b border-[#343434] mb-1">
                    Select Evaluator Persona
                  </div>

                  {(['teacher', 'student', 'advanced'] as const).map((role) => {
                    const RoleIcon = roleLabels[role].icon;
                    const isSelected = currentRole === role;

                    return (
                      <button
                        key={role}
                        onClick={() => handleRoleSelect(role)}
                        role="menuitem"
                        className={`w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between transition-colors ${
                          isSelected
                            ? 'bg-[#261214] border border-[#5C1D20] text-[#F5F2EF] font-semibold'
                            : 'hover:bg-[#282828] text-[#B7B3B0]'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <RoleIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-[#A31C1B]' : 'text-[#898582]'}`} />
                          <div>
                            <div className="font-medium text-[#F5F2EF]">{roleLabels[role].name}</div>
                            <div className="text-[11px] text-[#898582]">{roleLabels[role].title}</div>
                          </div>
                        </div>
                        {isSelected && <Check className="w-3.5 h-3.5 text-[#A31C1B]" />}
                      </button>
                    );
                  })}
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
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center space-x-1.5 ${
                    activeTab === 'ai-tutor' ? 'bg-[#261214] text-[#F5F2EF] border border-[#5C1D20]' : 'text-[#B7B3B0]'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#A31C1B]" />
                  <span>AI Tutor Workspace</span>
                </button>
                <button
                  onClick={() => handleNavClick('adaptive-quiz')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center space-x-1.5 ${
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
            <div className="grid grid-cols-1 gap-1.5">
              {(['teacher', 'student', 'advanced'] as const).map((role) => {
                const RoleIcon = roleLabels[role].icon;
                const isSelected = currentRole === role;

                return (
                  <button
                    key={role}
                    onClick={() => handleRoleSelect(role)}
                    className={`w-full text-left p-2.5 rounded-lg flex items-center justify-between text-xs transition-colors ${
                      isSelected
                        ? 'bg-[#261214] border border-[#5C1D20] text-[#F5F2EF] font-semibold'
                        : 'bg-[#202020] border border-[#343434] text-[#B7B3B0]'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <RoleIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-[#A31C1B]' : 'text-[#898582]'}`} />
                      <span>{roleLabels[role].name} ({roleLabels[role].title})</span>
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
