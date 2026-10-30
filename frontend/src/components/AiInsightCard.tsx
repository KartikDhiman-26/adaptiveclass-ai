import React, { useState } from 'react';
import { Lightbulb, ShieldCheck, ChevronDown, ChevronUp, AlertOctagon, Sparkles, Award } from 'lucide-react';
import { AiInsightResponse } from '../types';

interface AiInsightCardProps {
  insight: AiInsightResponse;
}

export const AiInsightCard: React.FC<AiInsightCardProps> = ({ insight }) => {
  const [showExplainability, setShowExplainability] = useState(false);

  return (
    <section 
      aria-label="Instructional Intelligence Briefing"
      className="bg-white rounded-2xl border border-stone-200/90 p-6 sm:p-7 shadow-sm relative overflow-hidden"
    >
      {/* Top Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-stone-100">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-md bg-stone-100 border border-stone-200 flex items-center justify-center text-stone-800">
            <Sparkles className="w-3.5 h-3.5 text-blue-900" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-semibold uppercase tracking-widest text-stone-500">
                Instructional Intelligence Briefing
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-stone-100 text-stone-600 border border-stone-200/60">
                {insight.generated_by}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={() => setShowExplainability(!showExplainability)}
          className="text-xs text-stone-700 hover:text-stone-900 font-medium flex items-center space-x-1.5 bg-stone-50 hover:bg-stone-100 px-3 py-1.5 rounded-lg border border-stone-200 transition-colors"
          aria-expanded={showExplainability}
        >
          <span>{showExplainability ? 'Hide Evidence & Metrics' : 'Examine Statistical Evidence'}</span>
          {showExplainability ? (
            <ChevronUp className="w-3.5 h-3.5 text-stone-500" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-stone-500" />
          )}
        </button>
      </div>

      {/* Primary Thesis / Core Diagnostic */}
      <div className="pt-5 pb-4">
        <div className="inline-flex items-center space-x-1.5 text-xs font-semibold text-red-800 bg-red-50 border border-red-200/70 px-2.5 py-0.5 rounded mb-2.5">
          <AlertOctagon className="w-3.5 h-3.5 text-red-700" />
          <span>Priority Curricular Gap Identified</span>
        </div>
        <h3 className="text-xl sm:text-2xl font-semibold text-stone-900 tracking-tight leading-snug">
          <span className="font-bold underline decoration-red-300 decoration-2 underline-offset-4">{insight.learning_gap}</span> represents the cohort's acute concept bottleneck at <span className="tabular-nums font-bold">{insight.class_mastery}%</span> mastery.
        </h3>
        <p className="mt-2 text-sm text-stone-600 leading-relaxed max-w-3xl">
          <strong className="text-stone-900 font-semibold">{insight.students_below_threshold} students</strong> scored below the 40% foundational competency threshold. Immediate instructional intervention is advised prior to progressing to dependent topics like tree traversals and dynamic recursion.
        </p>
      </div>

      {/* Two-Column Action Memorandum */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-3">
        {/* Intervention Plan */}
        <div className="bg-[#FAF9F6] border border-stone-200/90 rounded-xl p-4 sm:p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-blue-950 font-semibold text-xs tracking-wider uppercase mb-2">
              <Lightbulb className="w-4 h-4 text-blue-800" />
              <span>Recommended Revision Strategy</span>
            </div>
            <p className="text-sm text-stone-800 leading-relaxed">
              {insight.suggested_action}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-stone-200/60 text-[11px] text-stone-500">
            Target Audience: <strong>{insight.students_below_threshold} students</strong> needing foundational support
          </div>
        </div>

        {/* Enrichment Track */}
        <div className="bg-[#FAF9F6] border border-stone-200/90 rounded-xl p-4 sm:p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-stone-900 font-semibold text-xs tracking-wider uppercase mb-2">
              <Award className="w-4 h-4 text-stone-700" />
              <span>Parallel High-Mastery Challenge</span>
            </div>
            <p className="text-sm text-stone-800 leading-relaxed">
              {insight.enrichment_action}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-stone-200/60 text-[11px] text-stone-500">
            Target Audience: Advanced learners consistently demonstrating high mastery (≥85%)
          </div>
        </div>
      </div>

      {/* Collapsible Evidence & Methodology Drawer */}
      {showExplainability && (
        <div className="mt-4 pt-4 border-t border-stone-200 text-xs bg-stone-50/70 rounded-xl p-4 space-y-3">
          <div className="font-semibold text-stone-800 flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-blue-900" />
            <span className="text-xs uppercase tracking-wider">Data Verification & Grounding Trace</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-stone-700">
            <div className="bg-white p-3 rounded-lg border border-stone-200">
              <span className="font-semibold text-stone-900 block mb-1">Measured Gap (WHAT):</span>
              <p className="text-stone-600 leading-relaxed">{insight.what}</p>
            </div>
            <div className="bg-white p-3 rounded-lg border border-stone-200">
              <span className="font-semibold text-stone-900 block mb-1">Statistical Justification (WHY):</span>
              <p className="text-stone-600 leading-relaxed">{insight.why}</p>
            </div>
          </div>
          <p className="text-[11px] text-stone-500 italic pt-1">
            Grounded directly in measured assessment records across all 80 cohort entries in PostgreSQL. This diagnostic focuses purely on concept mastery and answer patterns without making speculative assumptions.
          </p>
        </div>
      )}

      {/* Teacher Agency Disclaimer */}
      <div className="mt-4 pt-3.5 border-t border-stone-100 flex items-center space-x-2 text-xs text-stone-500">
        <ShieldCheck className="w-4 h-4 text-stone-600 flex-shrink-0" />
        <span className="font-medium text-stone-600">{insight.teacher_disclaimer}</span>
      </div>
    </section>
  );
};
