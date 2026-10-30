import React, { useState } from 'react';
import { Search, RefreshCw, GraduationCap } from 'lucide-react';
import { StudentProfileResponse } from '../types';
import { StudentProfileModal } from '../components/StudentProfileModal';
import { api } from '../api';

interface StudentListPageProps {
  students: any[];
  onRefresh: () => void;
  isLoading: boolean;
  onSimulateStudent: (studentId: number) => void;
}

export const StudentListPage: React.FC<StudentListPageProps> = ({
  students,
  onRefresh,
  isLoading,
  onSimulateStudent
}) => {
  const [search, setSearch] = useState('');
  const [selectedTier, setSelectedTier] = useState<string>('all');
  const [selectedProfile, setSelectedProfile] = useState<StudentProfileResponse | null>(null);

  const handleOpenProfile = async (id: number) => {
    try {
      const p = await api.getStudentProfile(id);
      setSelectedProfile(p);
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = students.filter(s => {
    const matchesSearch = s.name.toLowerCase().includes(search.toLowerCase()) ||
                          s.roll_number.toLowerCase().includes(search.toLowerCase()) ||
                          s.email.toLowerCase().includes(search.toLowerCase());
    const matchesTier = selectedTier === 'all' || s.status_label.toLowerCase() === selectedTier.toLowerCase();
    return matchesSearch && matchesTier;
  });

  const getTierBadge = (tier: string) => {
    const t = tier.toLowerCase();
    if (t.includes('advanced')) return 'bg-[#0B1B14] text-emerald-300 border-[#20372B]';
    if (t.includes('on track')) return 'bg-[#14231C] text-emerald-200 border-[#20372B]';
    if (t.includes('support')) return 'bg-amber-950/60 text-amber-300 border-amber-800';
    return 'bg-[#261214] text-rose-300 border-[#5C1D20]';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* 1. Masthead & Controls */}
      <div className="bg-[#202020] rounded-2xl border border-[#343434] p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#C12A29] font-semibold mb-1">
            <span>Enrolled Roster Intelligence</span>
            <span>•</span>
            <span>80 Students</span>
          </div>
          <h1 className="text-2xl font-bold text-[#F5F2EF]">Student Roster & Diagnostic Telemetry</h1>
          <p className="text-xs text-[#B7B3B0] mt-0.5">Filter by performance tier or search individual learners</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-[#898582] absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search student or roll no..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-[#171717] border border-[#343434] rounded-xl text-xs text-[#F5F2EF] placeholder-[#898582] focus:outline-none focus:ring-1 focus:ring-[#A31C1B] w-64"
            />
          </div>

          <select
            value={selectedTier}
            onChange={(e) => setSelectedTier(e.target.value)}
            className="border border-[#343434] rounded-xl py-2 px-3 text-xs bg-[#171717] text-[#F5F2EF] focus:outline-none focus:ring-1 focus:ring-[#A31C1B]"
          >
            <option value="all">All Learning Tiers</option>
            <option value="advanced">Advanced (≥85%)</option>
            <option value="on track">On Track (55%-84%)</option>
            <option value="needs support">Needs Support (40%-54%)</option>
            <option value="needs attention">Needs Attention (&lt;40%)</option>
          </select>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 border border-[#343434] rounded-xl bg-[#171717] hover:bg-[#202020] text-[#B7B3B0] disabled:opacity-50"
            title="Refresh student roster"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 2. Students Table */}
      <div className="bg-[#202020] rounded-2xl border border-[#343434] overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#171717] text-[#898582] uppercase font-mono text-[10px] border-b border-[#343434]">
              <tr>
                <th className="py-3.5 px-4">Student</th>
                <th className="py-3.5 px-4">Roll Number</th>
                <th className="py-3.5 px-4">Cumulative Mastery</th>
                <th className="py-3.5 px-4">Achievement Tier</th>
                <th className="py-3.5 px-4">Identified Gap</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#343434] font-mono text-[#B7B3B0]">
              {filtered.map(s => {
                const isDemoAarav = s.email === 'student@demo.com';
                const isDemoPriya = s.email === 'advanced@demo.com';

                return (
                  <tr key={s.id} className="hover:bg-[#0B1B14] transition-colors">
                    <td className="py-3.5 px-4 font-sans">
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-[#F5F2EF]">{s.name}</span>
                        {isDemoAarav && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#261214] text-rose-300 border border-[#5C1D20]">
                            Demo Student
                          </span>
                        )}
                        {isDemoPriya && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0B1B14] text-emerald-300 border border-[#20372B]">
                            Demo Scholar
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-[#898582] font-mono">{s.email}</div>
                    </td>
                    <td className="py-3.5 px-4 text-[#898582]">
                      {s.roll_number}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-[#F5F2EF] tabular-nums text-sm">
                          {s.overall_mastery}%
                        </span>
                        <div className="w-16 bg-[#06110C] rounded-full h-1.5 overflow-hidden hidden sm:block border border-[#343434]">
                          <div 
                            className="h-full rounded-full bg-[#A31C1B]"
                            style={{ width: `${s.overall_mastery}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] uppercase font-bold border ${getTierBadge(s.status_label)}`}>
                        {s.status_label}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-[#C12A29] font-medium">
                        {s.weak_concept}
                      </span>
                      {s.weak_mastery !== undefined && (
                        <span className="text-[#898582] text-[11px] ml-1">
                          ({s.weak_mastery}%)
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleOpenProfile(s.id)}
                          className="px-3 py-1 rounded-lg bg-[#171717] hover:bg-[#202020] border border-[#343434] text-[#F5F2EF] hover:border-[#A31C1B] hover:text-[#C12A29] text-xs font-semibold transition-colors"
                        >
                          Profile
                        </button>
                        <button
                          onClick={() => onSimulateStudent(s.id)}
                          title="Simulate student session"
                          className="px-2.5 py-1 rounded-lg bg-[#261214] hover:bg-[#3B1517] text-[#C12A29] border border-[#5C1D20] text-xs font-semibold transition-colors"
                        >
                          <GraduationCap className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Profile Modal */}
      <StudentProfileModal
        profile={selectedProfile}
        onClose={() => setSelectedProfile(null)}
        onSimulateStudentPractice={onSimulateStudent}
      />
    </div>
  );
};
