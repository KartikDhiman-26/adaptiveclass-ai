import React, { useState } from 'react';
import { SubjectSummary, StudentNeedingAttentionItem, StudentProfileResponse } from '../types';
import { 
  ChevronLeft, AlertOctagon, 
  TrendingUp, Award, Users, GraduationCap
} from 'lucide-react';
import { StudentScoreDistribution } from '../components/StudentScoreDistribution';
import { StudentProfileModal } from '../components/StudentProfileModal';
import { api } from '../api';

interface SubjectReportViewProps {
  subject: SubjectSummary;
  attentionStudents: StudentNeedingAttentionItem[];
  onBackToOverview: () => void;
  onBackToDirectory: () => void;
  onSimulateStudent: (studentId: number) => void;
}

export const SubjectReportView: React.FC<SubjectReportViewProps> = ({
  subject,
  attentionStudents,
  onBackToOverview,
  onBackToDirectory,
  onSimulateStudent
}) => {
  const [selectedProfile, setSelectedProfile] = useState<StudentProfileResponse | null>(null);

  const handleOpenStudentProfile = async (studentId: number) => {
    try {
      const p = await api.getStudentProfile(studentId);
      setSelectedProfile(p);
    } catch (err) {
      console.error('Failed to load student profile:', err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-xs font-mono text-[#898582]">
        <button
          onClick={onBackToOverview}
          className="hover:text-[#C12A29] transition-colors flex items-center space-x-1"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
          <span>Class Overview</span>
        </button>
        <span>/</span>
        <button
          onClick={onBackToDirectory}
          className="hover:text-[#C12A29] transition-colors"
        >
          Subjects
        </button>
        <span>/</span>
        <span className="text-[#F5F2EF] font-semibold">{subject.code}</span>
      </nav>

      {/* 2. Subject Masthead */}
      <header className="bg-[#202020] rounded-2xl border border-[#343434] p-6 sm:p-7 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#C12A29] font-semibold">
              {subject.code} • {subject.semester}
            </span>
            <span className="text-[#898582]">•</span>
            <span className="text-[11px] text-[#B7B3B0] font-mono">{subject.department}</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-[#F5F2EF] tracking-tight mt-1">
            {subject.name}
          </h1>

          <p className="text-xs sm:text-sm text-[#B7B3B0] mt-1 flex flex-wrap items-center gap-x-2">
            <span>Enrolled: <strong className="text-[#F5F2EF]">{subject.studentCount} Students</strong></span>
            <span className="text-[#898582]">•</span>
            <span>Evaluated Topics: <strong className="text-[#F5F2EF]">{subject.topics.length} Concepts</strong></span>
            <span className="text-[#898582]">•</span>
            {subject.isLiveDb ? (
              <span className="inline-flex items-center space-x-1.5 text-emerald-300 font-mono text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Live PostgreSQL Diagnostics Active</span>
              </span>
            ) : (
              <span className="text-[#898582] font-mono text-xs">Curriculum Analytics Active</span>
            )}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => onSimulateStudent(1)}
            className="px-4 py-2.5 rounded-xl bg-[#A31C1B] hover:bg-[#C12A29] text-white font-semibold text-xs transition-colors shadow-sm flex items-center space-x-2"
          >
            <GraduationCap className="w-4 h-4" />
            <span>Simulate Practice Loop</span>
          </button>
        </div>
      </header>

      {/* 3. Executive KPI Strip */}
      <section aria-label="Subject Indicators">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#202020] rounded-xl border border-[#343434] p-5">
            <div className="flex items-center justify-between text-[#898582] text-xs font-mono uppercase tracking-wider">
              <span>Subject Average</span>
              <TrendingUp className="w-4 h-4 text-[#C12A29]" />
            </div>
            <div className="text-3xl font-bold font-mono text-[#F5F2EF] mt-2 tabular-nums">
              {subject.overallAverage}%
            </div>
            <span className="text-[11px] text-[#898582] font-mono mt-1 block">
              Across {subject.topics.length} tested competencies
            </span>
          </div>

          <div className="bg-[#261214] rounded-xl border border-[#5C1D20] p-5">
            <div className="flex items-center justify-between text-rose-300 text-xs font-mono uppercase tracking-wider">
              <span>Primary Bottleneck</span>
              <AlertOctagon className="w-4 h-4 text-[#C12A29]" />
            </div>
            <div className="text-xl font-bold font-mono text-rose-200 mt-2 truncate">
              {subject.weakestTopic}
            </div>
            <span className="text-[11px] text-[#C12A29] font-mono mt-1 block">
              {subject.weakestMastery}% ({subject.interventionCount} students below 40% bar)
            </span>
          </div>

          <div className="bg-[#0B1B14] rounded-xl border border-[#20372B] p-5">
            <div className="flex items-center justify-between text-emerald-300 text-xs font-mono uppercase tracking-wider">
              <span>Demonstrated Strength</span>
              <Award className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-xl font-bold font-mono text-emerald-200 mt-2 truncate">
              {subject.strongestTopic}
            </div>
            <span className="text-[11px] text-emerald-400 font-mono mt-1 block">
              {subject.strongestMastery}% mastery benchmark
            </span>
          </div>

          <div className="bg-[#202020] rounded-xl border border-[#343434] p-5">
            <div className="flex items-center justify-between text-[#898582] text-xs font-mono uppercase tracking-wider">
              <span>Intervention Priority</span>
              <Users className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-3xl font-bold font-mono text-amber-300 mt-2 tabular-nums">
              {subject.interventionCount}
            </div>
            <span className="text-[11px] text-[#898582] font-mono mt-1 block">
              Students requiring targeted review
            </span>
          </div>
        </div>
      </section>

      {/* 4. Evidence-Based Instructional Directive */}
      <section aria-label="AI Instructional Guidance">
        <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 sm:p-7 shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-[#A31C1B]" />
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#C12A29] font-semibold">
              Evidence-Based Instructional Guidance • {subject.code}
            </span>
          </div>

          <h3 className="text-lg font-bold text-[#F5F2EF]">
            {subject.instructionalRecommendations.title}
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-[#171717] rounded-xl border border-[#343434] space-y-2">
              <span className="text-amber-400 font-mono font-semibold uppercase tracking-wider text-[10px] block">
                Prescribed Classroom Action
              </span>
              <p className="text-[#B7B3B0] leading-relaxed">
                {subject.instructionalRecommendations.action}
              </p>
            </div>

            <div className="p-4 bg-[#171717] rounded-xl border border-[#343434] space-y-2">
              <span className="text-[#C12A29] font-mono font-semibold uppercase tracking-wider text-[10px] block">
                Pedagogical Rationale
              </span>
              <p className="text-[#B7B3B0] leading-relaxed">
                {subject.instructionalRecommendations.rationale}
              </p>
            </div>
          </div>

          <div className="p-3.5 bg-[#0B1B14] rounded-xl border border-[#20372B] flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-[#898582] font-mono text-[11px]">Enrichment Path:</span>
              <span className="text-emerald-300 font-mono text-[11px]">{subject.instructionalRecommendations.enrichmentPath}</span>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Topic Mastery Grid */}
      <section aria-label="Topic Breakdown" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-[#F5F2EF]">
            Topic Competency Breakdown
          </h2>
          <span className="text-xs font-mono text-[#898582]">
            {subject.topics.length} Evaluated Computational Modules
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {subject.topics.map((topic) => {
            const barWidth = `${topic.mastery}%`;
            const isCritical = topic.mastery < 40;
            const isStrong = topic.mastery >= 75;

            return (
              <div
                key={topic.id}
                className="bg-[#202020] rounded-xl border border-[#343434] p-5 space-y-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#898582]">
                      {topic.difficulty} difficulty
                    </span>
                    <span
                      className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded border ${
                        isCritical
                          ? 'bg-[#261214] text-rose-300 border-[#5C1D20]'
                          : isStrong
                          ? 'bg-[#0B1B14] text-emerald-300 border-[#20372B]'
                          : 'bg-[#14231C] text-emerald-200 border-[#20372B]'
                      }`}
                    >
                      {topic.status}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-[#F5F2EF] mt-1">
                    {topic.name}
                  </h3>

                  <p className="text-xs text-[#B7B3B0] mt-1 line-clamp-2 leading-relaxed">
                    {topic.description}
                  </p>
                </div>

                <div>
                  <div className="flex items-baseline justify-between text-xs font-mono mb-1.5">
                    <span className="text-[#898582] text-[11px]">Mastery Score</span>
                    <span className="text-base font-bold text-[#F5F2EF] tabular-nums">
                      {topic.mastery}%
                    </span>
                  </div>

                  <div className="w-full bg-[#06110C] rounded-full h-2 overflow-hidden border border-[#343434]">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isCritical
                          ? 'bg-[#A31C1B]'
                          : isStrong
                          ? 'bg-emerald-400'
                          : 'bg-emerald-600'
                      }`}
                      style={{ width: barWidth }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 6. Score Distribution for this subject */}
      <section aria-label="Subject Stratification">
        <StudentScoreDistribution distribution={subject.distribution} />
      </section>

      {/* 7. Students Needing Attention (for Data Structures / live DB) */}
      {subject.isLiveDb && attentionStudents.length > 0 && (
        <section aria-label="Students Requiring Intervention" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-[#F5F2EF]">
                Students Requiring Immediate Targeted Support ({attentionStudents.length})
              </h2>
              <p className="text-xs text-[#B7B3B0] mt-0.5">
                Students below the 40% mastery threshold in {subject.weakestTopic}
              </p>
            </div>
          </div>

          <div className="bg-[#202020] rounded-2xl border border-[#343434] overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#171717] text-[#898582] uppercase font-mono text-[10px] border-b border-[#343434]">
                  <tr>
                    <th className="py-3 px-4">Student</th>
                    <th className="py-3 px-4">Roll Number</th>
                    <th className="py-3 px-4">Primary Gap</th>
                    <th className="py-3 px-4">Gap Mastery</th>
                    <th className="py-3 px-4">Overall Mastery</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#343434] font-mono text-[#B7B3B0]">
                  {attentionStudents.slice(0, 10).map((s) => (
                    <tr key={s.student_id} className="hover:bg-[#0B1B14] transition-colors">
                      <td className="py-3 px-4 font-sans font-medium text-[#F5F2EF]">
                        {s.student_name}
                      </td>
                      <td className="py-3 px-4 text-[#898582]">
                        {s.roll_number}
                      </td>
                      <td className="py-3 px-4 text-[#C12A29] font-semibold">
                        {s.weak_concept}
                      </td>
                      <td className="py-3 px-4 text-rose-400 font-bold tabular-nums">
                        {s.mastery}%
                      </td>
                      <td className="py-3 px-4 text-[#B7B3B0] tabular-nums">
                        {s.mastery < 40 ? 'Needs Support' : 'Progressing'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleOpenStudentProfile(s.student_id)}
                          className="px-3 py-1 rounded-lg bg-[#171717] hover:bg-[#202020] hover:text-[#C12A29] border border-[#343434] text-[#F5F2EF] text-[11px] font-semibold transition-colors"
                        >
                          View Profile
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* Student Profile Modal */}
      <StudentProfileModal
        profile={selectedProfile}
        onClose={() => setSelectedProfile(null)}
        onSimulateStudentPractice={onSimulateStudent}
      />
    </div>
  );
};
