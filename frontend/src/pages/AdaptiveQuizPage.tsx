import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, XCircle, ArrowRight, Zap, RefreshCw, 
  HelpCircle, ChevronRight, Award, ShieldAlert, Sparkles 
} from 'lucide-react';
import { QuestionOut, QuizSubmitResponse } from '../types';
import { api } from '../api';

interface AdaptiveQuizPageProps {
  studentId: number;
  conceptId?: number;
  onCompleteQuiz: (results: QuizSubmitResponse) => void;
  onCancel: () => void;
}

interface AnswerHistory {
  question_id: number;
  selected_answer: string;
  is_correct: boolean;
}

export const AdaptiveQuizPage: React.FC<AdaptiveQuizPageProps> = ({
  studentId,
  conceptId,
  onCompleteQuiz,
  onCancel
}) => {
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState('');
  const [conceptName, setConceptName] = useState('Recursion');
  const [targetConceptId, setTargetConceptId] = useState<number>(1);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionOut | null>(null);
  const [questionIndex, setQuestionIndex] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState('beginner');

  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [answerFeedback, setAnswerFeedback] = useState<{
    is_correct: boolean;
    correct_answer: string;
    explanation: string;
    difficulty_change: string;
    next_question: QuestionOut | null;
    is_quiz_complete: boolean;
  } | null>(null);

  const [history, setHistory] = useState<AnswerHistory[]>([]);
  const [isSubmittingFinal, setIsSubmittingFinal] = useState(false);

  useEffect(() => {
    startQuiz();
  }, [studentId, conceptId]);

  const startQuiz = async () => {
    setLoading(true);
    try {
      const res = await api.startAdaptiveQuiz(studentId, conceptId);
      setSessionId(res.session_id);
      setConceptName(res.concept_name);
      setTargetConceptId(res.concept_id);
      setCurrentQuestion(res.current_question);
      setQuestionIndex(res.question_index);
      setTotalQuestions(res.total_questions);
      setDifficulty(res.difficulty);
      setHistory([]);
      setSelectedOption(null);
      setIsAnswerSubmitted(false);
      setAnswerFeedback(null);
    } catch (err) {
      console.error("Failed to start adaptive quiz:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (opt: string) => {
    if (isAnswerSubmitted) return;
    setSelectedOption(opt);
  };

  const handleSubmitAnswer = async () => {
    if (!selectedOption || !currentQuestion) return;

    setLoading(true);
    try {
      const answeredIds = history.map(h => h.question_id);
      const res = await api.getNextAdaptiveQuestion({
        student_id: studentId,
        concept_id: targetConceptId,
        current_question_id: currentQuestion.question_id,
        selected_option: selectedOption,
        current_difficulty: difficulty,
        question_index: questionIndex,
        answered_question_ids: answeredIds
      });

      setAnswerFeedback(res);
      setIsAnswerSubmitted(true);

      const newHistoryItem: AnswerHistory = {
        question_id: currentQuestion.question_id,
        selected_answer: selectedOption,
        is_correct: res.is_correct
      };
      setHistory(prev => [...prev, newHistoryItem]);
    } catch (err) {
      console.error("Failed to process question answer:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleNextOrFinish = async () => {
    if (!answerFeedback) return;

    if (answerFeedback.is_quiz_complete || questionIndex >= totalQuestions || !answerFeedback.next_question) {
      // Complete quiz and submit to backend for dynamic mastery update
      setIsSubmittingFinal(true);
      try {
        const finalHistory = [...history];
        const submitPayload = {
          student_id: studentId,
          concept_id: targetConceptId,
          quiz_title: `Adaptive Practice: ${conceptName}`,
          answers: finalHistory
        };
        const result = await api.submitQuiz(submitPayload);
        onCompleteQuiz(result);
      } catch (err) {
        console.error("Failed to submit completed quiz:", err);
      } finally {
        setIsSubmittingFinal(false);
      }
    } else {
      // Advance to next dynamically selected question
      setCurrentQuestion(answerFeedback.next_question);
      setDifficulty(answerFeedback.next_question.difficulty);
      setQuestionIndex(prev => prev + 1);
      setSelectedOption(null);
      setIsAnswerSubmitted(false);
      setAnswerFeedback(null);
    }
  };

  if (loading && !currentQuestion) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
        <p className="text-sm text-slate-500 font-medium">Initializing Adaptive Quiz engine from PostgreSQL questions...</p>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center">
        <ShieldAlert className="w-10 h-10 text-rose-500 mx-auto mb-2" />
        <p className="text-sm text-slate-700 font-semibold">No questions found for this concept.</p>
        <button
          onClick={onCancel}
          className="mt-4 px-4 py-2 rounded-lg bg-slate-900 text-white text-xs font-semibold"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const getDifficultyBadge = () => {
    switch (difficulty.toLowerCase()) {
      case 'beginner':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'intermediate':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'advanced':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Quiz Container Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-md overflow-hidden">
        {/* Top Progress & Difficulty Bar */}
        <div className="bg-slate-900 text-white p-5 border-b border-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-indigo-300 font-bold uppercase tracking-wider">
                {conceptName} Adaptive Practice
              </span>
              <span className="text-slate-500">•</span>
              <span className="text-xs text-slate-300 font-medium">
                Question {questionIndex} of {totalQuestions}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-[11px] text-slate-400">Current Difficulty:</span>
              <span className={`text-xs font-bold uppercase px-2.5 py-0.5 rounded-full border ${getDifficultyBadge()}`}>
                {difficulty}
              </span>
            </div>
          </div>

          {/* Animated Progress Bar */}
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-indigo-500 h-full transition-all duration-300 rounded-full"
              style={{ width: `${(questionIndex / totalQuestions) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Question Area */}
        <div className="p-6 space-y-6">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">
              Question #{questionIndex}
            </span>
            <h3 className="text-lg font-bold text-slate-900 leading-snug">
              {currentQuestion.question_text}
            </h3>
          </div>

          {/* Options */}
          <div className="space-y-3">
            {[
              { key: 'A', text: currentQuestion.option_a },
              { key: 'B', text: currentQuestion.option_b },
              { key: 'C', text: currentQuestion.option_c },
              { key: 'D', text: currentQuestion.option_d },
            ].map(opt => {
              const isSelected = selectedOption === opt.key;
              const isCorrectOpt = answerFeedback && answerFeedback.correct_answer.toUpperCase() === opt.key;
              const isWrongSelected = isAnswerSubmitted && isSelected && !answerFeedback?.is_correct;

              let cardStyle = 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50/50';
              if (isSelected && !isAnswerSubmitted) {
                cardStyle = 'border-indigo-600 bg-indigo-50/50 ring-1 ring-indigo-500';
              } else if (isCorrectOpt) {
                cardStyle = 'border-emerald-500 bg-emerald-50 text-emerald-950 font-medium ring-1 ring-emerald-500';
              } else if (isWrongSelected) {
                cardStyle = 'border-rose-500 bg-rose-50 text-rose-950 ring-1 ring-rose-500';
              }

              return (
                <div
                  key={opt.key}
                  onClick={() => handleSelectOption(opt.key)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${cardStyle}`}
                >
                  <div className="flex items-center space-x-3">
                    <span className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                      isSelected && !isAnswerSubmitted
                        ? 'bg-indigo-600 text-white'
                        : isCorrectOpt
                        ? 'bg-emerald-600 text-white'
                        : isWrongSelected
                        ? 'bg-rose-600 text-white'
                        : 'bg-slate-100 text-slate-700'
                    }`}>
                      {opt.key}
                    </span>
                    <span className="text-sm">{opt.text}</span>
                  </div>

                  {isCorrectOpt && (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  )}
                  {isWrongSelected && (
                    <XCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Feedback Card (After Answer Submission) */}
          {isAnswerSubmitted && answerFeedback && (
            <div className={`p-4 rounded-xl border animate-in fade-in duration-300 ${
              answerFeedback.is_correct
                ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                : 'bg-rose-50 border-rose-200 text-rose-950'
            }`}>
              <div className="flex items-center space-x-2 font-bold text-sm mb-1.5">
                {answerFeedback.is_correct ? (
                  <>
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <span>Correct Answer!</span>
                    <span className="text-xs bg-emerald-200 text-emerald-900 px-2 py-0.5 rounded-full ml-2">
                      Adaptive Difficulty: {answerFeedback.difficulty_change === 'increased' ? 'Escalated to Next Level' : 'Maintained'}
                    </span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-5 h-5 text-rose-600" />
                    <span>Incorrect — Let's Reinforce This Concept</span>
                    <span className="text-xs bg-rose-200 text-rose-900 px-2 py-0.5 rounded-full ml-2">
                      Adaptive Support Triggered
                    </span>
                  </>
                )}
              </div>

              <p className="text-xs text-slate-700 leading-relaxed mt-2 bg-white/70 p-2.5 rounded-lg border border-slate-200/60">
                <strong>Explanation:</strong> {answerFeedback.explanation}
              </p>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="bg-slate-50 px-6 py-4 border-t border-slate-200 flex items-center justify-between">
          <button
            onClick={onCancel}
            className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
          >
            Cancel Practice
          </button>

          {!isAnswerSubmitted ? (
            <button
              onClick={handleSubmitAnswer}
              disabled={!selectedOption || loading}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1.5"
            >
              <span>Submit Answer</span>
            </button>
          ) : (
            <button
              onClick={handleNextOrFinish}
              disabled={isSubmittingFinal}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition-all flex items-center space-x-1.5"
            >
              <span>
                {questionIndex >= totalQuestions || answerFeedback?.is_quiz_complete
                  ? (isSubmittingFinal ? 'Calculating Mastery...' : 'Finish & View Class Impact')
                  : 'Next Question (Adapted)'}
              </span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
