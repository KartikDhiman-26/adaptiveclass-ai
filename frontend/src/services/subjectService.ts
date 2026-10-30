import { SubjectSummary, ClassAnalyticsResponse } from '../types';

/**
 * Subject Service for AdaptiveClass AI
 * Sychronizes curriculum and subject diagnostics strictly from live PostgreSQL
 * database records. No synthetic or hardcoded engineering courses are injected.
 */

export const subjectService = {
  /**
   * Builds the comprehensive subject directory directly from PostgreSQL database classes
   * and the active class analytics payload.
   */
  getCurriculumSubjects: (
    dbClasses: any[] = [],
    liveAnalytics: ClassAnalyticsResponse | null
  ): SubjectSummary[] => {
    if (!liveAnalytics && (!dbClasses || dbClasses.length === 0)) {
      return [];
    }

    if (!liveAnalytics) {
      // Classes exist in DB, but analytics has not loaded yet
      return (dbClasses || []).map((c) => {
        const subName = c.subject || c.name || 'Subject';
        const code = (subName || 'SUB')
          .split(' ')
          .map((w: string) => w[0])
          .join('')
          .slice(0, 4)
          .toUpperCase() + `-${c.id}`;

        return {
          id: `class-${c.id}`,
          code,
          name: subName,
          department: c.name,
          semester: c.semester || 'Academic Session',
          studentCount: c.student_count || 0,
          overallAverage: 0,
          weakestTopic: 'Diagnostic pending',
          weakestMastery: 0,
          strongestTopic: 'Diagnostic pending',
          strongestMastery: 0,
          interventionCount: 0,
          isLiveDb: true,
          dbClassId: c.id,
          topics: [],
          distribution: {
            advanced: 0,
            on_track: 0,
            needs_support: 0,
            needs_attention: 0,
            total: c.student_count || 0
          },
          instructionalRecommendations: {
            title: `${c.name} (${subName})`,
            action: 'Select this cohort to load live diagnostic breakdown.',
            rationale: `Enrolled learners: ${c.student_count || 0} students.`,
            focusConcepts: [],
            enrichmentPath: 'Switch active cohort in dashboard.'
          }
        };
      });
    }

    // 1. Build Primary Active Subject from live PostgreSQL analytics
    const activeDbClass = (dbClasses || []).find((c) => c.id === liveAnalytics.class_id);
    const primarySubjectName = liveAnalytics.subject || activeDbClass?.subject || liveAnalytics.class_name;
    const primaryCode = (primarySubjectName || 'SUB')
      .split(' ')
      .map((w: string) => w[0])
      .join('')
      .slice(0, 4)
      .toUpperCase() + `-${liveAnalytics.class_id}`;

    // Map live concept mastery items from PostgreSQL
    const liveTopics = (liveAnalytics.concept_mastery || []).map((c) => {
      const mastery = Number(c.mastery_percentage) || 0;
      return {
        id: c.concept_id,
        name: c.concept_name,
        mastery,
        difficulty: (mastery < 45 ? 'beginner' : mastery < 70 ? 'intermediate' : 'advanced') as 'beginner' | 'intermediate' | 'advanced',
        status: (c.status_label || (mastery < 40 ? 'Critical Gap' : mastery < 55 ? 'Needs Attention' : mastery < 80 ? 'Moderate' : 'Strong')) as any,
        statusColor: (c.status_color || (mastery < 40 ? 'red' : mastery < 55 ? 'amber' : mastery < 80 ? 'blue' : 'green')) as any,
        questionCount: 5,
        description: `Curriculum topic: ${c.concept_name}. Measured cohort mastery: ${mastery}%.`
      };
    });

    const activeSubject: SubjectSummary = {
      id: `class-${liveAnalytics.class_id}`,
      code: primaryCode,
      name: primarySubjectName,
      department: liveAnalytics.class_name,
      semester: liveAnalytics.semester || activeDbClass?.semester || 'Academic Session',
      studentCount: liveAnalytics.student_count,
      overallAverage: liveAnalytics.overall_class_average,
      weakestTopic: liveAnalytics.weakest_concept || (liveTopics[0]?.name ?? 'None'),
      weakestMastery: liveTopics.find((t) => t.name === liveAnalytics.weakest_concept)?.mastery ?? (liveTopics[0]?.mastery ?? 0),
      strongestTopic: liveAnalytics.strongest_concept || (liveTopics[liveTopics.length - 1]?.name ?? 'None'),
      strongestMastery: liveTopics.find((t) => t.name === liveAnalytics.strongest_concept)?.mastery ?? (liveTopics[liveTopics.length - 1]?.mastery ?? 0),
      interventionCount: liveAnalytics.recursion_support_count,
      isLiveDb: true,
      dbClassId: liveAnalytics.class_id,
      topics: liveTopics,
      distribution: liveAnalytics.global_distribution || {
        advanced: 0,
        on_track: 0,
        needs_support: 0,
        needs_attention: 0,
        total: liveAnalytics.student_count
      },
      instructionalRecommendations: {
        title: liveAnalytics.ai_insight?.what || `Curriculum Analysis: ${primarySubjectName}`,
        action: liveAnalytics.ai_insight?.suggested_action || 'Review foundational concept competencies with guided practice.',
        rationale: liveAnalytics.ai_insight?.why || `${liveAnalytics.recursion_support_count} students currently flagged below mastery threshold.`,
        focusConcepts: [liveAnalytics.weakest_concept].filter(Boolean),
        enrichmentPath: liveAnalytics.ai_insight?.enrichment_action || 'Provide advanced inquiry challenges for high-mastery learners.'
      }
    };

    // 2. Additional Cohort Subjects from other real classes in PostgreSQL
    const otherCohortSubjects: SubjectSummary[] = (dbClasses || [])
      .filter((c) => c.id !== liveAnalytics.class_id)
      .map((c) => {
        const subName = c.subject || c.name || 'Subject';
        const code = (subName || 'SUB')
          .split(' ')
          .map((w: string) => w[0])
          .join('')
          .slice(0, 4)
          .toUpperCase() + `-${c.id}`;

        return {
          id: `class-${c.id}`,
          code,
          name: subName,
          department: c.name,
          semester: c.semester || 'Academic Session',
          studentCount: c.student_count || 0,
          overallAverage: 0,
          weakestTopic: 'Cohort Overview',
          weakestMastery: 0,
          strongestTopic: 'Cohort Overview',
          strongestMastery: 0,
          interventionCount: 0,
          isLiveDb: true,
          dbClassId: c.id,
          topics: [],
          distribution: {
            advanced: 0,
            on_track: 0,
            needs_support: 0,
            needs_attention: 0,
            total: c.student_count || 0
          },
          instructionalRecommendations: {
            title: `${c.name} (${subName})`,
            action: 'Select this cohort from the cohort selector to view live diagnostic breakdown.',
            rationale: `Enrolled learners: ${c.student_count || 0} students.`,
            focusConcepts: [],
            enrichmentPath: 'Switch active cohort in dashboard.'
          }
        };
      });

    return [activeSubject, ...otherCohortSubjects];
  }
};
