import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Send, ArrowRight, BookOpen, AlertOctagon, 
  RotateCcw, Code2, ShieldCheck, ArrowLeft, BarChart2,
  RefreshCw, UserCheck, AlertTriangle
} from 'lucide-react';
import { TutorMessage, QuickPromptType, TutorConcept } from '../types/tutor';
import { tutorService, QUICK_PROMPTS } from '../services/tutorService';
import { api } from '../api';
import { StudentProfileResponse } from '../types';

interface AiTutorPageProps {
  studentId: number;
  initialConceptId?: number;
  onStartPractice: (conceptId?: number, topicName?: string) => void;
  onViewProgress: () => void;
}

export const AiTutorPage: React.FC<AiTutorPageProps> = ({
  studentId,
  initialConceptId,
  onStartPractice,
  onViewProgress
}) => {
  const [profile, setProfile] = useState<StudentProfileResponse | null>(null);
  const [studentToken, setStudentToken] = useState<string | null>(null);
  const [concepts, setConcepts] = useState<TutorConcept[]>([]);
  const [selectedConcept, setSelectedConcept] = useState<TutorConcept | null>(null);
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<{ text: string; promptType: QuickPromptType } | null>(null);
  const [tutorEngineStatus, setTutorEngineStatus] = useState<{ gemini_configured: boolean; model: string; mode: string } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  // Initial load / student change: fetch profile and student bearer token
  useEffect(() => {
    if (!studentId) {
      setProfile(null);
      setStudentToken(null);
      setSessionId(null);
      const defaults = tutorService.getConceptsForStudent(null);
      setConcepts(defaults);
      setSelectedConcept(defaults[0]);
      setMessages(tutorService.getInitialWorkspaceMessages(defaults[0].name, 'Student', defaults[0].mastery));
      return;
    }

    let isMounted = true;
    setApiError(null);
    setSessionId(null); // Fresh session for switched student identity

    // 1. Fetch real student profile, bearer token, and tutor engine status concurrently
    Promise.all([
      api.getStudentProfile(studentId),
      api.getStudentToken(studentId).catch((err) => {
        console.warn('Could not auto-fetch token for student:', err);
        return null;
      }),
      api.getTutorStatus().catch(() => ({
        gemini_configured: false,
        model: 'gemini-3.5-flash-lite',
        mode: 'offline (pedagogical engine fallback)',
        active_engine: 'offline_fallback'
      }))
    ])
      .then(([p, tokenData, statusData]) => {
        if (!isMounted) return;
        if (statusData) {
          setTutorEngineStatus(statusData);
        }
        setProfile(p);
        if (tokenData && tokenData.token) {
          setStudentToken(tokenData.token);
        }

        const derivedConcepts = tutorService.getConceptsForStudent(p);
        setConcepts(derivedConcepts);

        // Find initial concept or default to priority learning gap
        let target = derivedConcepts.find((c) => c.id === initialConceptId);
        if (!target) {
          target =
            derivedConcepts.find((c) => c.name.toLowerCase() === p.current_learning_gap.toLowerCase()) ||
            derivedConcepts[0];
        }
        setSelectedConcept(target);
        setMessages(tutorService.getInitialWorkspaceMessages(target.name, p.student_name, target.mastery));
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load student profile for AI tutor:', err);
        setApiError(`Could not load student profile: ${err.message || 'Network error'}`);
        const defaults = tutorService.getConceptsForStudent(null);
        setConcepts(defaults);
        setSelectedConcept(defaults[0]);
        setMessages(tutorService.getInitialWorkspaceMessages(defaults[0].name, 'Student', defaults[0].mastery));
      });

    return () => {
      isMounted = false;
    };
  }, [studentId, initialConceptId]);

  // Auto-scroll chat to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // Handle switching active concept
  const handleSelectConcept = (concept: TutorConcept) => {
    if (selectedConcept?.id === concept.id) return;
    setSelectedConcept(concept);
    setSessionId(null); // Start fresh multi-turn session for the new concept
    setApiError(null);
    const studentName = profile?.student_name || 'Student';
    setMessages(tutorService.getInitialWorkspaceMessages(concept.name, studentName, concept.mastery));
  };

  // Submit query to live backend
  const handleSendMessage = async (textToSend: string, promptType: QuickPromptType = 'custom') => {
    if (!textToSend.trim() || isThinking || !selectedConcept) return;

    if (!studentId) {
      setApiError('Please select a student persona before sending a query to the AI Tutor.');
      return;
    }

    const trimmedText = textToSend.trim();
    const userMessage: TutorMessage = {
      id: `usr_${Date.now()}`,
      role: 'student',
      content: trimmedText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      quickPromptType: promptType
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsThinking(true);
    setApiError(null);
    setLastFailedMessage(null);

    try {
      // Ensure we have a valid bearer token
      let token = studentToken;
      if (!token) {
        const tokenRes = await api.getStudentToken(studentId);
        token = tokenRes.token;
        setStudentToken(token);
      }

      const response = await tutorService.sendMessage(
        selectedConcept.name,
        trimmedText,
        promptType,
        studentId,
        profile?.student_name,
        token,
        sessionId,
        selectedConcept.id
      );

      // Persist session ID returned by PostgreSQL backend for multi-turn retention
      if (response.sessionId) {
        setSessionId(response.sessionId);
      }

      setMessages((prev) => [...prev, response]);
    } catch (err: any) {
      console.error('Error getting real tutor response:', err);
      const errMsg = err?.message || 'Failed to communicate with AI Tutor API';
      setApiError(errMsg);
      setLastFailedMessage({ text: trimmedText, promptType });

      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'tutor',
          content: `⚠️ **Connection Notice**: I was unable to connect to the backend tutor engine.\n\n*Error details*: ${errMsg}\n\nPlease verify that the FastAPI backend is running and click retry below.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true
        }
      ]);
    } finally {
      setIsThinking(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  // Trigger quick prompt
  const handleQuickPromptClick = (prompt: typeof QUICK_PROMPTS[number]) => {
    if (!selectedConcept) return;
    const query = prompt.queryTemplate(selectedConcept.name);
    handleSendMessage(query, prompt.id);
  };

  // Reset conversation for active concept
  const handleResetConversation = () => {
    if (!selectedConcept) return;
    setSessionId(null);
    setApiError(null);
    const studentName = profile?.student_name || 'Student';
    setMessages(tutorService.getInitialWorkspaceMessages(selectedConcept.name, studentName, selectedConcept.mastery));
  };

  // Render markdown text and embedded code blocks
  const renderMessageContent = (content: string) => {
    const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
    const parts: Array<{ type: 'text' | 'code'; language?: string; content: string }> = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: content.slice(lastIndex, match.index)
        });
      }
      parts.push({
        type: 'code',
        language: match[1] || 'text',
        content: match[2].trim()
      });
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < content.length) {
      parts.push({
        type: 'text',
        content: content.slice(lastIndex)
      });
    }

    return (
      <div className="space-y-3">
        {parts.map((p, idx) => {
          if (p.type === 'code') {
            return (
              <div key={idx} className="my-3 rounded-xl bg-[#171717] text-[#F5F2EF] p-3.5 border border-[#343434] font-mono text-xs overflow-x-auto">
                <div className="flex justify-between items-center text-[10px] text-[#898582] mb-2 border-b border-[#343434] pb-1.5 uppercase tracking-widest font-mono">
                  <span>{p.language || 'code'} trace</span>
                  <Code2 className="w-3.5 h-3.5 text-[#898582]" />
                </div>
                <pre className="font-mono text-xs leading-relaxed text-emerald-300">
                  <code>{p.content}</code>
                </pre>
              </div>
            );
          }
          return (
            <div key={idx} className="whitespace-pre-wrap leading-relaxed">
              {p.content}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* 1. TOP DARK BANNER & BREADCRUMBS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#343434]">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#898582] mb-1">
            <button 
              onClick={onViewProgress}
              className="hover:text-[#C12A29] transition-colors flex items-center space-x-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Learning Portal</span>
            </button>
            <span>/</span>
            <span className="text-[#F5F2EF] font-medium">1-on-1 Socratic Learning Room</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F5F2EF] tracking-tight flex items-center space-x-2.5">
            <span>Socratic Study Companion</span>
          </h1>
          <p className="text-xs text-[#B7B3B0] mt-0.5">
            Real-time emotion-aware pedagogical dialog connected to FastAPI and Gemini with full multi-turn persistence.
          </p>
          <div className="flex items-center space-x-2 mt-2">
            {tutorEngineStatus?.gemini_configured ? (
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono bg-[#0B1B14] text-emerald-400 border border-emerald-800/60 shadow-sm">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                <span>Live Gemini Active ({tutorEngineStatus.model})</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono bg-[#1c1811] text-amber-300 border border-amber-900/60 shadow-sm" title="Offline pedagogical engine active. Set GEMINI_API_KEY in backend/.env for live Gemini.">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                <span>Offline Pedagogical Mode (Set GEMINI_API_KEY for Live Gemini)</span>
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onViewProgress}
            className="px-3.5 py-2 rounded-xl border border-[#343434] bg-[#171717] hover:bg-[#202020] text-xs font-medium text-[#B7B3B0] hover:text-[#F5F2EF] transition-colors shadow-sm flex items-center space-x-1.5"
          >
            <BarChart2 className="w-3.5 h-3.5 text-[#898582]" />
            <span>View Progress</span>
          </button>

          {selectedConcept && (
            <button
              onClick={() => onStartPractice(selectedConcept.id, selectedConcept.name)}
              className="px-4 py-2 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] text-white font-semibold text-xs shadow-sm transition-all flex items-center space-x-1.5"
            >
              <BookOpen className="w-3.5 h-3.5 text-white" />
              <span>Practice {selectedConcept.name}</span>
              <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
            </button>
          )}
        </div>
      </div>

      {/* Global Error Banner if API Fails */}
      {apiError && (
        <div className="p-3.5 rounded-xl bg-[#261214] border border-[#A31C1B]/60 text-xs text-rose-200 flex items-center justify-between gap-3 animate-in fade-in">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-[#C12A29] flex-shrink-0" />
            <span>{apiError}</span>
          </div>
          {lastFailedMessage && (
            <button
              onClick={() => handleSendMessage(lastFailedMessage.text, lastFailedMessage.promptType)}
              className="px-2.5 py-1 rounded bg-[#A31C1B] hover:bg-[#C12A29] text-white text-[11px] font-mono flex items-center space-x-1 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          )}
        </div>
      )}

      {/* 2. MAIN WORKSPACE: SIDEBAR + CHAT STAGE */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Left Column: Concept Selector & Curriculum Context */}
        <aside aria-label="Curriculum Concept Selector" className="lg:col-span-1 space-y-4">
          <div className="bg-[#202020] rounded-2xl border border-[#343434] p-5 shadow-sm space-y-4">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[#C12A29] font-mono block mb-1">
                Select Active Focus
              </span>
              <h3 className="text-sm font-bold text-[#F5F2EF]">
                Core Curricular Concepts
              </h3>
            </div>

            <div className="space-y-1.5">
              {concepts.map((c) => {
                const isSelected = selectedConcept?.id === c.id;
                const isGap = c.mastery < 40;

                return (
                  <button
                    key={c.id}
                    onClick={() => handleSelectConcept(c)}
                    className={`w-full text-left p-3 rounded-xl border text-xs transition-all flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#261214] text-white border-[#A31C1B]/60 shadow-sm'
                        : 'bg-[#171717] hover:bg-[#0B1B14] text-[#B7B3B0] border-[#343434] hover:border-[#20372B]'
                    }`}
                  >
                    <div>
                      <div className="font-semibold flex items-center space-x-1.5">
                        <span>{c.name}</span>
                        {isGap && !isSelected && (
                          <AlertOctagon className="w-3 h-3 text-[#C12A29] flex-shrink-0" />
                        )}
                      </div>
                      <span className={`text-[10px] font-mono block mt-0.5 ${isSelected ? 'text-rose-200' : 'text-[#898582]'}`}>
                        {c.status}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className={`font-mono font-bold tabular-nums ${
                        isSelected 
                          ? 'text-white' 
                          : isGap 
                          ? 'text-[#C12A29]' 
                          : 'text-[#F5F2EF]'
                      }`}>
                        {c.mastery}%
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Active Concept Micro-Summary */}
            {selectedConcept && (
              <div className="pt-4 border-t border-[#343434] text-xs text-[#B7B3B0] space-y-2">
                <div>
                  <span className="text-[11px] font-semibold uppercase text-[#F5F2EF] font-mono block">Topic Scope:</span>
                  <p className="mt-0.5 text-[#B7B3B0] leading-relaxed text-[11px]">
                    {selectedConcept.description}
                  </p>
                </div>
                <div>
                  <span className="text-[11px] font-semibold uppercase text-[#F5F2EF] font-mono block">Key Modules:</span>
                  <ul className="mt-1 space-y-1 text-[11px] text-[#898582] font-mono">
                    {selectedConcept.recommendedTopics.map((topic, i) => (
                      <li key={i} className="flex items-center space-x-1.5">
                        <span className="w-1 h-1 rounded-full bg-[#A31C1B]" />
                        <span>{topic}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Persona Sync & Architecture Status */}
          <div className="bg-[#0B1B14] border border-[#20372B] rounded-xl p-3.5 text-[11px] text-[#B7B3B0] space-y-1.5">
            <div className="flex items-center space-x-1.5 text-[#F5F2EF] font-semibold font-mono">
              <UserCheck className="w-3.5 h-3.5 text-[#C12A29] flex-shrink-0" />
              <span>Persona Sync</span>
            </div>
            <p className="leading-relaxed">
              Active identity: <strong className="text-[#F5F2EF]">{profile?.student_name || 'Loading student...'}</strong>
            </p>
            <p className="text-[10px] text-[#898582] font-mono">
              Role: student • ID: {studentId} • Token: {studentToken ? 'Authenticated' : 'Resolving'}
            </p>
          </div>
        </aside>

        {/* Right Column: Conversational Learning Stage */}
        <section 
          aria-label="Tutor Conversation Stage"
          className="lg:col-span-3 bg-[#202020] rounded-2xl border border-[#343434] shadow-sm flex flex-col h-[740px] overflow-hidden"
        >
          {/* Stage Header */}
          <div className="bg-[#171717] px-6 py-4 border-b border-[#343434] flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-[#0B1B14] border border-[#20372B] text-emerald-400 flex items-center justify-center font-bold text-xs">
                AI
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-sm font-bold text-[#F5F2EF]">
                    {selectedConcept ? `${selectedConcept.name} Study Thread` : 'Concept Study'}
                  </h2>
                  {selectedConcept && (
                    <span className={`text-[11px] px-2 py-0.5 rounded font-mono font-medium border ${
                      selectedConcept.mastery < 40 
                        ? 'bg-[#261214] text-rose-300 border-[#5C1D20]' 
                        : 'bg-[#202020] text-[#B7B3B0] border-[#343434]'
                    }`}>
                      {selectedConcept.mastery}% Mastery
                    </span>
                  )}
                  {sessionId && (
                    <span className="hidden sm:inline text-[10px] text-[#898582] font-mono border border-[#343434] px-1.5 py-0.5 rounded bg-[#171717]">
                      Thread #{sessionId.slice(0, 8)}
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#898582]">
                  Select a prompt below or type any question to trace execution step-by-step
                </p>
              </div>
            </div>

            <button
              onClick={handleResetConversation}
              title="Reset conversation back to beginning"
              className="text-[#898582] hover:text-[#F5F2EF] p-1.5 rounded-lg hover:bg-[#202020] transition-colors text-xs flex items-center space-x-1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reset Thread</span>
            </button>
          </div>

          {/* Quick Prompts Drawer */}
          <div className="bg-[#171717] px-6 py-3 border-b border-[#343434]">
            <div className="flex items-center space-x-2 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-[#C12A29]" />
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[#898582] font-mono">
                Quick Pedagogical Prompts
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt.id}
                  onClick={() => handleQuickPromptClick(prompt)}
                  disabled={isThinking}
                  className="p-2 text-left bg-[#202020] hover:bg-[#0B1B14] border border-[#343434] hover:border-[#20372B] rounded-lg transition-all group disabled:opacity-50"
                >
                  <span className="font-semibold text-[#F5F2EF] text-xs block group-hover:text-[#C12A29] transition-colors">
                    {prompt.label}
                  </span>
                  <span className="text-[10px] text-[#898582] block line-clamp-1">
                    {prompt.description}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Scrollable Chat Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-[#06110C]">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.role === 'student' ? 'items-end' : 'items-start'}`}
              >
                {/* Message Header Bar */}
                <div className="flex flex-wrap items-center gap-2 mb-1.5 px-1">
                  <span className="text-[11px] font-semibold text-[#898582] uppercase font-mono">
                    {msg.role === 'student' ? (profile?.student_name || 'You') : 'Pedagogical Socratic Tutor'}
                  </span>
                  <span className="text-[10px] text-[#898582] font-mono">{msg.timestamp}</span>

                  {/* Explicit Engine Badge */}
                  {msg.role === 'tutor' && msg.engineUsed && (
                    <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${
                      msg.engineUsed === 'gemini'
                        ? 'bg-[#0B1B14] text-emerald-400 border-emerald-800/60'
                        : 'bg-[#1c1811] text-amber-300 border-amber-900/60'
                    }`}>
                      {msg.engineUsed === 'gemini' ? (
                        <>
                          <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
                          <span>Gemini Live ({tutorEngineStatus?.model || 'Flash'})</span>
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-2.5 h-2.5 text-amber-400" />
                          <span>Offline Fallback Engine</span>
                        </>
                      )}
                    </span>
                  )}

                  {/* Emotion / Pedagogical Adaptation Badge */}
                  {msg.role === 'tutor' && msg.adaptationApplied && (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-[#202020] text-[#B7B3B0] border border-[#343434]">
                      <span>💡 {msg.adaptationApplied}</span>
                    </span>
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  className={`max-w-2xl rounded-2xl p-4 sm:p-5 text-xs sm:text-sm leading-relaxed border ${
                    msg.role === 'student'
                      ? 'bg-[#A31C1B] text-white border-[#C12A29] rounded-tr-sm shadow-sm'
                      : msg.isError
                      ? 'bg-[#261214] text-rose-200 border-[#A31C1B]/80 rounded-tl-sm shadow-sm'
                      : 'bg-[#202020] text-[#F5F2EF] border-[#343434] rounded-tl-sm shadow-sm'
                  }`}
                >
                  {/* Content paragraphs and formatted code */}
                  {renderMessageContent(msg.content)}

                  {/* Diagnostic Quiz Suggestion Card */}
                  {msg.suggestQuiz && (
                    <div className="mt-4 p-3 rounded-xl bg-[#0B1B14] border border-[#20372B] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                      <div className="space-y-0.5">
                        <span className="text-[11px] font-mono font-semibold text-emerald-400 uppercase tracking-wider block">
                          Diagnostic Check Ready
                        </span>
                        <p className="text-xs text-[#F5F2EF]">
                          Ready to test your understanding of <strong className="text-white">{msg.suggestedQuizTopic || selectedConcept?.name}</strong>?
                        </p>
                      </div>
                      <button
                        onClick={() => onStartPractice(selectedConcept?.id, msg.suggestedQuizTopic)}
                        className="px-3.5 py-1.5 rounded-lg bg-[#A31C1B] hover:bg-[#C12A29] text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors whitespace-nowrap"
                      >
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>Launch Adaptive Quiz</span>
                        <ArrowRight className="w-3 h-3 ml-0.5" />
                      </button>
                    </div>
                  )}

                  {/* Suggested practice CTA if present and quiz not already suggested */}
                  {msg.suggestedAction && !msg.suggestQuiz && (
                    <div className="mt-4 pt-3 border-t border-[#343434] flex items-center justify-between gap-2">
                      <span className="text-[11px] text-[#898582] font-medium">Ready to test this concept?</span>
                      <button
                        onClick={() => onStartPractice(msg.suggestedAction?.conceptId || selectedConcept?.id, msg.suggestedAction?.topicName)}
                        className="px-3 py-1.5 rounded-lg bg-[#A31C1B] hover:bg-[#C12A29] text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                      >
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>{msg.suggestedAction.label}</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Socratic Dynamic Follow-up Suggestions */}
                {msg.followUpQuestions && msg.followUpQuestions.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5 max-w-2xl">
                    {msg.followUpQuestions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSendMessage(q, 'custom')}
                        disabled={isThinking}
                        className="text-[11px] font-mono text-[#B7B3B0] bg-[#171717] hover:bg-[#202020] border border-[#343434] hover:border-[#20372B] rounded-full px-3 py-1 transition-colors flex items-center space-x-1 group"
                      >
                        <span className="text-[#C12A29] group-hover:translate-x-0.5 transition-transform">→</span>
                        <span>{q}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Thinking / formulation indicator */}
            {isThinking && (
              <div className="flex flex-col items-start animate-in fade-in duration-150">
                <span className="text-[11px] font-semibold text-[#898582] uppercase font-mono mb-1">
                  Pedagogical Tutor
                </span>
                <div className="bg-[#202020] border border-[#343434] rounded-2xl rounded-tl-sm p-4 text-xs text-[#B7B3B0] flex items-center space-x-2 shadow-sm">
                  <div className="flex space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#A31C1B] animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#A31C1B] animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#A31C1B] animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-[11px] text-[#898582] font-mono">Formulating Socratic response...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Message Composer */}
          <div className="bg-[#171717] p-4 border-t border-[#343434]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(inputText, 'custom');
              }}
              className="flex items-end gap-3"
            >
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(inputText, 'custom');
                    }
                  }}
                  rows={2}
                  placeholder={`Ask anything about ${selectedConcept?.name || 'this concept'} (e.g., "Why does base case matter?", "Can you trace an example?")...`}
                  className="w-full p-3 rounded-xl border border-[#343434] bg-[#202020] text-xs text-[#F5F2EF] placeholder-[#898582] focus:outline-none focus:ring-1 focus:ring-[#A31C1B] resize-none transition-colors"
                />
                <span className="absolute right-3 bottom-2 text-[10px] text-[#898582] font-mono hidden sm:inline">
                  Enter to send • Shift+Enter for new line
                </span>
              </div>

              <button
                type="submit"
                disabled={!inputText.trim() || isThinking}
                className="px-4 py-3 bg-[#A31C1B] hover:bg-[#C12A29] text-white rounded-xl text-xs font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1.5 shadow-sm h-12"
              >
                <span>Ask</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
};
