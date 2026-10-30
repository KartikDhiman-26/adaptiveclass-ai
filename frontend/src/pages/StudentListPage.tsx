import React, { useState } from 'react';
import { Search, Filter, RefreshCw, User, Award, AlertTriangle } from 'lucide-react';
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Student Roster & Individual Mastery</h1>
          <p className="text-xs text-slate-500 mt-0.5">Full cohort of 80 enrolled engineering students</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search student or roll no..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-xs w-64 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <select
            value={selectedTier}
            onChange={(e) => setSelectedTier(e.target.value)}
            className="border border-slate-200 rounded-lg py-2 px-3 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
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
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Student</th>
                <th className="py-3 px-4">Roll Number</th>
                <th className="py-3 px-4">Overall Mastery</th>
                <th className="py-3 px-4">Status Tier</th>
                <th className="py-3 px-4">Weakest Concept</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map(s => (
                <tr key={s.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-900">{s.name}</div>
                    <div className="text-[11px] text-slate-400">{s.email}</div>
                  </td>
                  <td className="py-3 px-4 text-slate-600 font-mono">
                    {s.roll_number}
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-900">
                    {s.overall_mastery}%
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                      s.status_label === 'Advanced' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                      s.status_label === 'On Track' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                      s.status_label === 'Needs Support' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                      'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      {s.status_label}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-medium text-slate-700">
                      {s.weak_concept} ({s.weak_mastery}%)
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleOpenProfile(s.id)}
                      className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded text-xs font-semibold transition-colors"
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

      <StudentProfileModal
        profile={selectedProfile}
        onClose={() => setSelectedProfile(null)}
        onSimulateStudentPractice={(id) => {
          setSelectedProfile(null);
          onSimulateStudent(id);
        }}
      />
    </div>
  );
};
