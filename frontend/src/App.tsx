import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { ClassOverviewPage } from './pages/ClassOverviewPage';
import { SubjectDirectoryPage } from './pages/SubjectDirectoryPage';
import { SubjectReportView } from './pages/SubjectReportView';
import { StudentListPage } from './pages/StudentListPage';
import { InsightsPage } from './pages/InsightsPage';
import { StudentDashboard } from './pages/StudentDashboard';
import { AdaptiveQuizPage } from './pages/AdaptiveQuizPage';
import { QuizResultsPage } from './pages/QuizResultsPage';
import { AiTutorPage } from './pages/AiTutorPage';
import { DataUploadModal } from './components/DataUploadModal';
import { 
  ClassAnalyticsResponse, StudentNeedingAttentionItem, 
  QuizSubmitResponse, SubjectSummary 
} from './types';
import { api } from './api';
import { subjectService } from './services/subjectService';
import { Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<'teacher' | 'student' | 'advanced'>('teacher');
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('cs-201-data-structures');
  const [activeStudentId, setActiveStudentId] = useState<number>(1); // Set dynamically from PostgreSQL

  const [analytics, setAnalytics] = useState<ClassAnalyticsResponse | null>(null);
  const [attentionStudents, setAttentionStudents] = useState<StudentNeedingAttentionItem[]>([]);
  const [studentsList, setStudentsList] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<SubjectSummary[]>([]);

  const [quizResults, setQuizResults] = useState<QuizSubmitResponse | null>(null);
  const [quizConceptId, setQuizConceptId] = useState<number | undefined>(undefined);
  const [tutorConceptId, setTutorConceptId] = useState<number | undefined>(undefined);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  const loadClassAndAnalytics = async () => {
    setIsLoading(true);
    try {
      // 1. Fetch classes from PostgreSQL
      const classes = await api.getClasses();
      const targetClassId = classes.length > 0 ? classes[0].id : 6;

      // 2. Fetch analytics and attention students in parallel from PostgreSQL
      const [analyticsData, attentionData, studentsData] = await Promise.all([
        api.getClassAnalytics(targetClassId),
        api.getStudentsNeedingAttention(targetClassId),
        api.getClassStudents(targetClassId)
      ]);

      setAnalytics(analyticsData);
      setAttentionStudents(attentionData);
      setStudentsList(studentsData);

      // 3. Synthesize curriculum subjects combining live DB and curriculum overviews
      const curriculumSubjects = subjectService.getCurriculumSubjects(classes, analyticsData);
      setSubjects(curriculumSubjects);

      // 4. Resolve demo student IDs dynamically from PostgreSQL
      if (studentsData && studentsData.length > 0) {
        const aarav = studentsData.find((s: any) => s.email === 'student@demo.com');
        const priya = studentsData.find((s: any) => s.email === 'advanced@demo.com');

        if (currentRole === 'advanced' && priya) {
          setActiveStudentId(priya.id);
        } else if (aarav) {
          setActiveStudentId(aarav.id);
        } else {
          setActiveStudentId(studentsData[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load class analytics:", err);
      showToast("Error connecting to backend or PostgreSQL. Ensure backend is running.");
      // Fallback subjects for offline preview
      const fallback = subjectService.getCurriculumSubjects([], null);
      setSubjects(fallback);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial Data Fetch
  useEffect(() => {
    loadClassAndAnalytics();
  }, []);

  const handleRoleChange = (role: 'teacher' | 'student' | 'advanced') => {
    setCurrentRole(role);
    if (role === 'teacher') {
      setActiveTab('dashboard');
    } else if (role === 'student') {
      const aarav = studentsList.find(s => s.email === 'student@demo.com');
      if (aarav) setActiveStudentId(aarav.id);
      setActiveTab('student-dashboard');
    } else if (role === 'advanced') {
      const priya = studentsList.find(s => s.email === 'advanced@demo.com');
      if (priya) setActiveStudentId(priya.id);
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
    await loadClassAndAnalytics();
    setActiveTab('quiz-results');
  };

  const handleViewTeacherDashboardFromResults = async () => {
    setCurrentRole('teacher');
    setActiveTab('dashboard');
    await loadClassAndAnalytics();
    showToast("Live sync: Class Overview updated from PostgreSQL with recent practice!");
  };

  const handleSelectSubject = (subjectId: string) => {
    setSelectedSubjectId(subjectId);
    setActiveTab('subject-report');
  };

  const handleNavigateToTab = (tab: string, subjectId?: string) => {
    if (subjectId) {
      setSelectedSubjectId(subjectId);
    }
    setActiveTab(tab);
  };

  // Find currently selected subject summary
  const currentSubject = subjects.find(s => s.id === selectedSubjectId) || subjects[0] || null;

  return (
    <div className="min-h-screen bg-[#171717] flex flex-col font-sans text-[#F5F2EF]">
      {/* Toast Banner */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 z-50 bg-[#202020] text-[#F5F2EF] px-4 py-3 rounded-xl shadow-2xl border border-[#343434] flex items-center space-x-2 text-xs animate-in slide-in-from-bottom-5">
          <Sparkles className="w-4 h-4 text-[#C12A29] flex-shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Navigation Bar with Sliding Indicator */}
      <Navbar
        currentRole={currentRole}
        onRoleChange={handleRoleChange}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        onResetDemo={handleResetDemo}
        isResetting={isResetting}
      />

      {/* Main Section Content */}
      <main className="flex-1 page-transition" key={activeTab}>
        {/* Landing Page (Overview) */}
        {activeTab === 'landing' && (
          <LandingPage
            onSelectRole={handleRoleChange}
            onNavigateToTab={handleNavigateToTab}
            subjects={subjects}
          />
        )}

        {/* 1. Class Overview */}
        {activeTab === 'dashboard' && (
          <ClassOverviewPage
            subjects={subjects}
            distribution={analytics?.global_distribution || {
              advanced: 12,
              on_track: 45,
              needs_support: 18,
              needs_attention: 5,
              total: 80
            }}
            attentionStudents={attentionStudents}
            isLoading={isLoading}
            onRefresh={loadClassAndAnalytics}
            onSelectSubject={handleSelectSubject}
            onViewAllSubjects={() => setActiveTab('subjects')}
            onViewStudents={() => setActiveTab('students')}
            onViewInsights={() => setActiveTab('insights')}
            onSimulateStudent={(sId) => {
              setActiveStudentId(sId);
              setCurrentRole('student');
              setActiveTab('student-dashboard');
            }}
            onOpenUploadModal={() => setIsUploadModalOpen(true)}
          />
        )}

        {/* 2. Subjects Directory */}
        {activeTab === 'subjects' && (
          <SubjectDirectoryPage
            subjects={subjects}
            onSelectSubject={handleSelectSubject}
            onBackToOverview={() => setActiveTab('dashboard')}
          />
        )}

        {/* Individual Subject Report View */}
        {activeTab === 'subject-report' && currentSubject && (
          <SubjectReportView
            subject={currentSubject}
            attentionStudents={attentionStudents}
            onBackToOverview={() => setActiveTab('dashboard')}
            onBackToDirectory={() => setActiveTab('subjects')}
            onSimulateStudent={(sId) => {
              setActiveStudentId(sId);
              setCurrentRole('student');
              setActiveTab('student-dashboard');
            }}
          />
        )}

        {/* 3. Students Roster */}
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

        {/* 4. Insights & Interventions */}
        {activeTab === 'insights' && (
          <InsightsPage
            subjects={subjects}
            onOpenSubjectReport={handleSelectSubject}
            onSimulatePractice={(sId) => {
              setActiveStudentId(sId);
              setCurrentRole('student');
              setActiveTab('student-dashboard');
            }}
          />
        )}

        {/* Student Learning Portal */}
        {activeTab === 'student-dashboard' && (
          <StudentDashboard
            studentId={activeStudentId}
            onStartQuiz={handleStartPractice}
            onOpenTutor={(conceptId) => {
              setTutorConceptId(conceptId);
              setActiveTab('ai-tutor');
            }}
          />
        )}

        {/* AI Tutor Socratic Workspace */}
        {activeTab === 'ai-tutor' && (
          <AiTutorPage
            studentId={activeStudentId}
            initialConceptId={tutorConceptId}
            onStartPractice={(conceptId) => handleStartPractice(conceptId)}
            onViewProgress={() => setActiveTab('student-dashboard')}
          />
        )}

        {/* Adaptive Practice Quiz */}
        {activeTab === 'adaptive-quiz' && (
          <AdaptiveQuizPage
            studentId={activeStudentId}
            conceptId={quizConceptId}
            onCompleteQuiz={handleCompleteQuiz}
            onCancel={() => setActiveTab('student-dashboard')}
          />
        )}

        {/* Quiz Results with Closed Feedback Loop */}
        {activeTab === 'quiz-results' && quizResults && (
          <QuizResultsPage
            results={quizResults}
            onViewTeacherDashboard={handleViewTeacherDashboardFromResults}
            onReturnToStudentDashboard={() => setActiveTab('student-dashboard')}
          />
        )}
      </main>

      {/* Dataset Upload Modal */}
      <DataUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={(dataset) => {
          showToast(`Dataset "${dataset.filename}" (${dataset.rows} records) successfully imported and validated!`);
          loadClassAndAnalytics();
        }}
      />

      {/* Dark Footer */}
      <footer className="bg-[#06110C] border-t border-[#343434] py-6 text-center text-xs text-[#898582]">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2 font-mono text-[11px]">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-[#F5F2EF]">AdaptiveClass AI</span>
            <span>•</span>
            <span className="text-[#B7B3B0]">Autonomous Learning Intelligence</span>
          </div>
          <div className="text-[#898582]">
            PostgreSQL 17 • FastAPI • React 19 + TypeScript • Precision Palette
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
