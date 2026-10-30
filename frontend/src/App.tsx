import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { TeacherDashboard } from './pages/TeacherDashboard';
import { StudentDashboard } from './pages/StudentDashboard';
import { StudentListPage } from './pages/StudentListPage';
import { AdaptiveQuizPage } from './pages/AdaptiveQuizPage';
import { QuizResultsPage } from './pages/QuizResultsPage';
import { ClassAnalyticsResponse, StudentNeedingAttentionItem, QuizSubmitResponse } from './types';
import { api } from './api';
import { Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<'teacher' | 'student' | 'advanced'>('teacher');
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [classId, setClassId] = useState<number>(1);
  const [activeStudentId, setActiveStudentId] = useState<number>(1); // Aarav Sharma by default

  const [analytics, setAnalytics] = useState<ClassAnalyticsResponse | null>(null);
  const [attentionStudents, setAttentionStudents] = useState<StudentNeedingAttentionItem[]>([]);
  const [studentsList, setStudentsList] = useState<any[]>([]);

  const [quizResults, setQuizResults] = useState<QuizSubmitResponse | null>(null);
  const [quizConceptId, setQuizConceptId] = useState<number | undefined>(undefined);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Initial Data Fetch
  useEffect(() => {
    loadClassAndAnalytics();
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  const loadClassAndAnalytics = async () => {
    setIsLoading(true);
    try {
      // 1. Fetch classes
      const classes = await api.getClasses();
      const targetClassId = classes.length > 0 ? classes[0].id : 1;
      setClassId(targetClassId);

      // 2. Fetch analytics and attention students in parallel from PostgreSQL
      const [analyticsData, attentionData, studentsData] = await Promise.all([
        api.getClassAnalytics(targetClassId),
        api.getStudentsNeedingAttention(targetClassId),
        api.getClassStudents(targetClassId)
      ]);

      setAnalytics(analyticsData);
      setAttentionStudents(attentionData);
      setStudentsList(studentsData);
    } catch (err) {
      console.error("Failed to load class analytics:", err);
      showToast("Error connecting to backend or PostgreSQL. Ensure backend is running.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRoleChange = (role: 'teacher' | 'student' | 'advanced') => {
    setCurrentRole(role);
    if (role === 'teacher') {
      setActiveTab('dashboard');
    } else if (role === 'student') {
      // Aarav Sharma
      const aarav = studentsList.find(s => s.email === 'student@demo.com');
      setActiveStudentId(aarav ? aarav.id : 1);
      setActiveTab('student-dashboard');
    } else if (role === 'advanced') {
      // Priya Patel
      const priya = studentsList.find(s => s.email === 'advanced@demo.com');
      setActiveStudentId(priya ? priya.id : 5);
      setActiveTab('student-dashboard');
    }
  };

  const handleResetDemo = async () => {
    setIsResetting(true);
    try {
      await api.resetDemoData();
      await loadClassAndAnalytics();
      setQuizResults(null);
      showToast("Demo reset: 80 students calibrated, Aarav Recursion reset to 28%, 23 students needing support.");
    } catch (err) {
      console.error("Failed to reset demo:", err);
      showToast("Failed to reset demo data.");
    } finally {
      setIsResetting(false);
    }
  };

  const handleStartPractice = (conceptId?: number) => {
    setQuizConceptId(conceptId);
    setActiveTab('adaptive-quiz');
  };

  const handleCompleteQuiz = async (results: QuizSubmitResponse) => {
    setQuizResults(results);
    // Reload backend analytics from PostgreSQL so latest data is cached
    await loadClassAndAnalytics();
    setActiveTab('quiz-results');
  };

  const handleViewTeacherDashboardFromResults = async () => {
    setCurrentRole('teacher');
    setActiveTab('dashboard');
    await loadClassAndAnalytics();
    showToast("Live sync: Teacher Dashboard updated from PostgreSQL with recent practice!");
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Toast Banner */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-xl border border-slate-700 flex items-center space-x-2 text-xs animate-in slide-in-from-bottom-5">
          <Sparkles className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Navigation */}
      <Navbar
        currentRole={currentRole}
        onRoleChange={handleRoleChange}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        onResetDemo={handleResetDemo}
        isResetting={isResetting}
      />

      {/* Main View Router */}
      <main className="flex-1">
        {activeTab === 'landing' && (
          <LandingPage
            onSelectRole={(role) => handleRoleChange(role)}
          />
        )}

        {activeTab === 'dashboard' && analytics && (
          <TeacherDashboard
            analytics={analytics}
            attentionStudents={attentionStudents}
            onRefresh={loadClassAndAnalytics}
            isLoading={isLoading}
            onSimulateStudent={(sId) => {
              setActiveStudentId(sId);
              setCurrentRole('student');
              setActiveTab('student-dashboard');
            }}
          />
        )}

        {activeTab === 'students' && (
          <StudentListPage
            students={studentsList}
            onRefresh={loadClassAndAnalytics}
            isLoading={isLoading}
            onSimulateStudent={(sId) => {
              setActiveStudentId(sId);
              setCurrentRole('student');
              setActiveTab('student-dashboard');
            }}
          />
        )}

        {activeTab === 'student-dashboard' && (
          <StudentDashboard
            studentId={activeStudentId}
            onStartQuiz={handleStartPractice}
          />
        )}

        {activeTab === 'adaptive-quiz' && (
          <AdaptiveQuizPage
            studentId={activeStudentId}
            conceptId={quizConceptId}
            onCompleteQuiz={handleCompleteQuiz}
            onCancel={() => setActiveTab('student-dashboard')}
          />
        )}

        {activeTab === 'quiz-results' && quizResults && (
          <QuizResultsPage
            results={quizResults}
            onViewTeacherDashboard={handleViewTeacherDashboardFromResults}
            onReturnToStudentDashboard={() => setActiveTab('student-dashboard')}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <strong>AdaptiveClass AI</strong> • B.E. CSE Data Structures Adaptive Learning Platform
          </div>
          <div className="text-slate-400">
            PostgreSQL 17 Database • FastAPI • React + Vite • Gemini 2.5 Flash / Deterministic Engine
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
