import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, XCircle, ArrowRight, Zap, RefreshCw, 
  ShieldAlert, Sparkles 
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

  const startQuiz = async () => {
    setLoading(true);
    try {
      const res = await api.startAdaptiveQuiz(studentId, conceptId);
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

  useEffect(() => {
    startQuiz();
  }, [studentId, conceptId]);

  const handleSelectOption = (opt: string) => {
    if (isAnswerSubmitted) return;
    setSelectedOption(opt);
  };

  const handleSubmitAnswer = async () => {
    if (!selectedOption || !currentQuestion || isAnswerSubmitted) return;

    try {
      const payload = {
        student_id: studentId,
        concept_id: targetConceptId,
        current_question_id: currentQuestion.question_id,
        selected_option: selectedOption,
        current_difficulty: difficulty,
        question_index: questionIndex,
        answered_question_ids: history.map(h => h.question_id)
      };

      const res = await api.getNextAdaptiveQuestion(payload);

      setAnswerFeedback({
        is_correct: res.is_correct,
        correct_answer: res.correct_answer,
        explanation: res.explanation,
        difficulty_change: res.difficulty_change,
        next_question: res.next_question,
        is_quiz_complete: res.is_quiz_complete
      });

      setIsAnswerSubmitted(true);

      setHistory(prev => [
        ...prev,
        {
          question_id: currentQuestion.question_id,
          selected_answer: selectedOption,
          is_correct: res.is_correct
        }
      ]);
    } catch (err) {
      console.error("Error submitting answer:", err);
    }
  };

  const handleProceedNext = async () => {
    if (!answerFeedback) return;

    if (answerFeedback.is_quiz_complete || questionIndex >= totalQuestions) {
      setIsSubmittingFinal(true);
      try {
        const finalPayload = {
          student_id: studentId,
          concept_id: targetConceptId,
          quiz_title: `${conceptName} Adaptive Mastery Assessment`,
          answers: history
        };
        const submitRes = await api.submitQuiz(finalPayload);
        onCompleteQuiz(submitRes);
      } catch (err) {
        console.error("Error submitting final quiz:", err);
      } finally {
        setIsSubmittingFinal(false);
      }
    } else if (answerFeedback.next_question) {
      setCurrentQuestion(answerFeedback.next_question);
      setQuestionIndex(prev => prev + 1);
      setDifficulty(answerFeedback.next_question.difficulty);
      setSelectedOption(null);
      setIsAnswerSubmitted(false);
      setAnswerFeedback(null);
    }
  };

  if (loading && !currentQuestion) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-3">
        <RefreshCw className="w-8 h-8 text-[#C12A29] animate-spin mx-auto" />
        <p className="text-sm text-[#898582] font-mono">Initializing Adaptive Practice engine from PostgreSQL questions...</p>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center space-y-3">
        <ShieldAlert className="w-10 h-10 text-rose-400 mx-auto" />
        <p className="text-sm text-[#F5F2EF] font-semibold">No questions found for this concept.</p>
        <button
          onClick={onCancel}
          className="mt-4 px-4 py-2 rounded-xl bg-[#202020] border border-[#343434] text-[#F5F2EF] text-xs font-semibold hover:bg-[#171717]"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const getDifficultyBadge = () => {
    switch (difficulty.toLowerCase()) {
      case 'beginner':
        return 'bg-[#0B1B14] text-emerald-300 border-[#20372B]';
      case 'intermediate':
        return 'bg-[#14231C] text-emerald-200 border-[#20372B]';
      case 'advanced':
        return 'bg-[#261214] text-rose-300 border-[#5C1D20]';
      default:
        return 'bg-[#171717] text-[#B7B3B0] border-[#343434]';
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Quiz Container Card */}
      <div className="bg-[#202020] rounded-2xl border border-[#343434] shadow-xl overflow-hidden">
        {/* Top Progress & Difficulty Bar */}
        <div className="bg-[#171717] text-[#F5F2EF] p-5 border-b border-[#343434]">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-[#C12A29] font-mono font-bold uppercase tracking-wider">
                {conceptName} Adaptive Practice
              </span>
              <span className="text-[#898582]">•</span>
              <span className="text-xs text-[#B7B3B0] font-mono">
                Question {questionIndex} of {totalQuestions}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-[11px] text-[#898582] font-mono">Current Difficulty:</span>
              <span className={`text-xs font-bold uppercase font-mono px-2.5 py-0.5 rounded-full border ${getDifficultyBadge()}`}>
                {difficulty}
              </span>
            </div>
          </div>

          {/* Animated Progress Bar */}
          <div className="w-full bg-[#06110C] rounded-full h-1.5 overflow-hidden border border-[#343434]">
            <div
              className="bg-[#A31C1B] h-full transition-all duration-300 rounded-full"
              style={{ width: `${(questionIndex / totalQuestions) * 100}%` }}
            />
          </div>
        </div>

        {/* Question Area */}
        <div className="p-6 sm:p-7 space-y-6">
          <div className="space-y-1">
            <span className="text-xs font-mono font-semibold text-[#C12A29] uppercase tracking-wide">
              Question #{questionIndex}
            </span>
            <h3 className="text-lg font-bold text-[#F5F2EF] leading-snug">
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

              let cardStyle = 'border-[#343434] bg-[#171717] hover:bg-[#0B1B14] hover:border-[#20372B] text-[#B7B3B0]';
              if (isSelected && !isAnswerSubmitted) {
                cardStyle = 'border-[#A31C1B] bg-[#261214] text-white ring-1 ring-[#A31C1B]';
              } else if (isCorrectOpt) {
                cardStyle = 'border-emerald-500 bg-[#0B1B14] text-emerald-200 ring-1 ring-emerald-500 font-medium';
              } else if (isWrongSelected) {
                cardStyle = 'border-rose-500 bg-[#261214] text-rose-200 ring-1 ring-rose-500';
              }

              return (
                <div
                  key={opt.key}
                  onClick={() => handleSelectOption(opt.key)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${cardStyle}`}
                >
                  <div className="flex items-center space-x-3">
                    <span className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs font-mono ${
                      isSelected && !isAnswerSubmitted
                        ? 'bg-[#A31C1B] text-white'
                        : isCorrectOpt
                        ? 'bg-emerald-500 text-slate-950'
                        : isWrongSelected
                        ? 'bg-[#7F1717] text-white'
                        : 'bg-[#202020] text-[#B7B3B0]'
                    }`}>
                      {opt.key}
                    </span>
                    <span className="text-xs sm:text-sm">{opt.text}</span>
                  </div>

                  {isCorrectOpt && <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />}
                  {isWrongSelected && <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />}
                </div>
              );
            })}
          </div>

          {/* Feedback Explanation Card */}
          {answerFeedback && (
            <div className={`p-4 sm:p-5 rounded-xl border text-xs sm:text-sm animate-in fade-in duration-200 space-y-2 ${
              answerFeedback.is_correct
                ? 'bg-[#0B1B14] border-[#20372B] text-emerald-200'
                : 'bg-[#261214] border-[#5C1D20] text-rose-200'
            }`}>
              <div className="flex items-center space-x-2 font-bold font-mono">
                {answerFeedback.is_correct ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Correct Analysis!</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 text-[#C12A29]" />
                    <span>Misconception Detected. Correct Answer is {answerFeedback.correct_answer}</span>
                  </>
                )}
              </div>

              <p className="text-xs text-[#B7B3B0] leading-relaxed font-sans">
                {answerFeedback.explanation}
              </p>

              <div className="pt-2 flex items-center space-x-2 text-xs font-mono text-[#898582]">
                <Zap className="w-3.5 h-3.5 text-[#C12A29]" />
                <span>
                  Adaptive Engine: Difficulty {answerFeedback.difficulty_change} for next question.
                </span>
              </div>
            </div>
          )}

          {/* Actions Bar */}
          <div className="pt-4 border-t border-[#343434] flex items-center justify-between">
            <button
              onClick={onCancel}
              className="text-xs font-mono text-[#898582] hover:text-[#F5F2EF] transition-colors"
            >
              Cancel Practice
            </button>

            {!isAnswerSubmitted ? (
              <button
                onClick={handleSubmitAnswer}
                disabled={!selectedOption}
                className="px-6 py-2.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-xs shadow-sm transition-all flex items-center space-x-1.5"
              >
                <span>Check Answer</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleProceedNext}
                disabled={isSubmittingFinal}
                className="px-6 py-2.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] text-white font-bold text-xs shadow-sm transition-all flex items-center space-x-1.5"
              >
                {isSubmittingFinal ? (
                  <span>Recording in PostgreSQL...</span>
                ) : questionIndex >= totalQuestions ? (
                  <>
                    <span>Submit Assessment</span>
                    <Sparkles className="w-4 h-4" />
                  </>
                ) : (
                  <>
                    <span>Next Adaptive Question</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
