import React, { useState } from 'react';
import { Bot, Lightbulb, ShieldCheck, ChevronDown, ChevronUp, AlertCircle, Sparkles, Award } from 'lucide-react';
import { AiInsightResponse } from '../types';

interface AiInsightCardProps {
  insight: AiInsightResponse;
}

export const AiInsightCard: React.FC<AiInsightCardProps> = ({ insight }) => {
  const [showExplainability, setShowExplainability] = useState(false);

  return (
    <div className="bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-indigo-800/40 relative overflow-hidden">
      {/* Decorative background glow */}
      <div className="absolute -top-24 -right-24 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* Card Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">AI Classroom Insight</span>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-900/60 border border-indigo-700/50 text-indigo-200">
                {insight.generated_by}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={() => setShowExplainability(!showExplainability)}
          className="text-xs text-indigo-300 hover:text-white flex items-center space-x-1 bg-indigo-900/40 hover:bg-indigo-900/70 px-2.5 py-1 rounded-md border border-indigo-700/40 transition-colors"
        >
          <span>{showExplainability ? 'Hide Evidence & Metrics' : 'Why this insight? (Explainability)'}</span>
          {showExplainability ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Main Core Alert */}
      <div className="mb-4">
        <h3 className="text-lg sm:text-xl font-bold text-white tracking-tight flex items-center space-x-2">
          <span className="text-rose-400 font-semibold">{insight.learning_gap}</span>
          <span>is currently the largest learning gap.</span>
        </h3>
        <div className="flex flex-wrap items-center gap-3 mt-1.5 text-sm text-slate-300">
          <span className="flex items-center space-x-1 text-rose-300 font-medium">
            <AlertCircle className="w-4 h-4 text-rose-400" />
            <span>{insight.class_mastery}% class mastery</span>
          </span>
          <span className="text-slate-500">•</span>
          <span className="text-amber-300 font-medium">
            {insight.students_below_threshold} students are below the support threshold
          </span>
        </div>
      </div>

      {/* Recommended Teacher Action Callout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
        <div className="bg-indigo-900/30 border border-indigo-700/40 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-indigo-300 font-semibold text-xs uppercase tracking-wide mb-1.5">
            <Lightbulb className="w-4 h-4 text-amber-300" />
            <span>Recommended Teacher Action</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">
            {insight.suggested_action}
          </p>
        </div>

        <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-emerald-300 font-semibold text-xs uppercase tracking-wide mb-1.5">
            <Award className="w-4 h-4 text-emerald-400" />
            <span>Advanced Enrichment Action</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">
            {insight.enrichment_action}
          </p>
        </div>
      </div>

      {/* Explainability Accordion */}
      {showExplainability && (
        <div className="mt-4 pt-4 border-t border-indigo-800/40 text-xs bg-slate-950/40 rounded-lg p-3">
          <div className="font-semibold text-indigo-200 mb-2 flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Data-Grounded Explainability Proof</span>
          </div>
          <div className="space-y-2 text-slate-300">
            <div>
              <span className="font-semibold text-slate-400">WHAT:</span> {insight.what}
            </div>
            <div>
              <span className="font-semibold text-slate-400">WHY:</span> {insight.why}
            </div>
            <div className="text-[11px] text-slate-400 italic">
              Computed from 80 student records in PostgreSQL. This model identifies performance patterns based on measured quiz accuracy and concept mastery scores without making personal or non-academic claims.
            </div>
          </div>
        </div>
      )}

      {/* Teacher Agency Disclaimer */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center space-x-2 text-[11px] text-slate-400">
        <ShieldCheck className="w-4 h-4 text-indigo-400 flex-shrink-0" />
        <span>{insight.teacher_disclaimer}</span>
      </div>
    </div>
  );
};
