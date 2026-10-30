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
import { api, normalizeClassId, ClassIdentifier } from './api';
import { subjectService } from './services/subjectService';
import { Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<'teacher' | 'student'>('teacher');
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('cs-201-data-structures');
  const [activeStudentId, setActiveStudentId] = useState<number | null>(null);
  const [classList, setClassList] = useState<any[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);

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

  const loadClassAndAnalytics = async (overrideClassRef?: ClassIdentifier | unknown) => {
    setIsLoading(true);
    try {
      // 1. Fetch classes from PostgreSQL
      const classes = await api.getClasses();
      setClassList(classes);
      // Defensively parse overrideClassRef (ignore DOM/React events and invalid inputs)
      let validOverrideId: number | undefined = undefined;
      if (overrideClassRef !== undefined && overrideClassRef !== null) {
        try {
          validOverrideId = normalizeClassId(overrideClassRef);
        } catch {
          validOverrideId = undefined;
        }
      }

      // Defensively parse existing selectedClassId
      let safeSelectedId: number | undefined = undefined;
      if (selectedClassId !== undefined && selectedClassId !== null) {
        try {
          safeSelectedId = normalizeClassId(selectedClassId);
        } catch {
          safeSelectedId = undefined;
        }
      }

      const defaultClassId = classes.length > 0 && classes[0]?.id ? normalizeClassId(classes[0].id) : 1;
      const activeClassId = validOverrideId ?? safeSelectedId ?? defaultClassId;
      setSelectedClassId(activeClassId);

      // 2. Fetch analytics and attention students in parallel from PostgreSQL
      const [analyticsData, attentionData, studentsData] = await Promise.all([
        api.getClassAnalytics(activeClassId),
        api.getStudentsNeedingAttention(activeClassId),
        api.getClassStudents(activeClassId)
      ]);

      setAnalytics(analyticsData);
      setAttentionStudents(attentionData);
      setStudentsList(studentsData);

      // 3. Synthesize curriculum subjects combining live DB and curriculum overviews
      const curriculumSubjects = subjectService.getCurriculumSubjects(classes, analyticsData);
      setSubjects(curriculumSubjects);

      // 4. Synchronize active student with the cohort
      if (studentsData && studentsData.length > 0) {
        const studentStillInCohort = studentsData.find((s: any) => s.id === activeStudentId);
        if (!studentStillInCohort) {
          // Default to a student needing support, or the first student in the cohort
          const supportStudent = studentsData.find((s: any) => s.overall_mastery < 55);
          setActiveStudentId(supportStudent ? supportStudent.id : studentsData[0].id);
        }
      } else {
        setActiveStudentId(null);
      }
    } catch (err) {
      console.error("Failed to load class analytics:", err);
      showToast("Error connecting to backend or PostgreSQL. Ensure backend is running.");
      const fallback = subjectService.getCurriculumSubjects([], null);
      setSubjects(fallback);
      setActiveStudentId(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial Data Fetch
  useEffect(() => {
    loadClassAndAnalytics();
  }, []);

  const activeStudent = studentsList.find((s: any) => s.id === activeStudentId) || (studentsList.length > 0 ? studentsList[0] : null);

  const handleRoleChange = (role: 'teacher' | 'student' | 'advanced', studentId?: number) => {
    if (role === 'teacher') {
      setCurrentRole('teacher');
      setActiveTab('dashboard');
    } else if (role === 'advanced') {
      setCurrentRole('student');
      const advancedStudent = studentsList.find((s: any) => s.overall_mastery >= 85) || (studentsList.length > 0 ? studentsList[0] : null);
      if (advancedStudent) setActiveStudentId(advancedStudent.id);
      setActiveTab('student-dashboard');
    } else {
      setCurrentRole('student');
      if (studentId) {
        setActiveStudentId(studentId);
      } else {
        const supportStudent = studentsList.find((s: any) => s.overall_mastery < 55) || (studentsList.length > 0 ? studentsList[0] : null);
        if (supportStudent) {
          setActiveStudentId(supportStudent.id);
        } else if (studentsList.length > 0) {
          setActiveStudentId(studentsList[0].id);
        }
      }
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
        activeStudent={activeStudent}
        studentsList={studentsList}
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
            analytics={analytics}
            distribution={analytics?.global_distribution || {
              advanced: 0,
              on_track: 0,
              needs_support: 0,
              needs_attention: 0,
              total: 0




            }}
            attentionStudents={attentionStudents}
            isLoading={isLoading}
            onRefresh={() => loadClassAndAnalytics()}
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
            classList={classList}
            selectedClassId={selectedClassId}
            onSelectClass={(id: number) => loadClassAndAnalytics(id)}
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
            onRefresh={() => loadClassAndAnalytics()}
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
            studentId={activeStudentId || 0}
            className={classList.find(c => c.id === selectedClassId)?.name}
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
            studentId={activeStudentId || 0}
            initialConceptId={tutorConceptId}
            onStartPractice={(conceptId) => handleStartPractice(conceptId)}
            onViewProgress={() => setActiveTab('student-dashboard')}
          />
        )}

        {/* Adaptive Practice Quiz */}
        {activeTab === 'adaptive-quiz' && (
          <AdaptiveQuizPage
            studentId={activeStudentId || 0}
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
          showToast(`Dataset "${dataset.filename}" (${dataset.rows.toLocaleString()} records) successfully imported! Switched to ${dataset.class_name || 'imported cohort'}.`);
          if (dataset.class_id) {
            loadClassAndAnalytics(dataset.class_id);
          } else {
            loadClassAndAnalytics();
          }
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
