import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';
import { attendanceApi, leaveApi } from '../api/client';

export default function EmployeeDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [recentLeaves, setRecentLeaves] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statRes, leaveRes] = await Promise.all([
          attendanceApi.todayStatus(),
          leaveApi.list(),
        ]);
        setStatus(statRes.data);
        setRecentLeaves(leaveRes.data.slice(0, 3));
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    };
    fetchData();

    window.addEventListener('attendance-update', fetchData);
    return () => window.removeEventListener('attendance-update', fetchData);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/signin');
  };

  const cards = [
    {
      title: 'My Profile',
      desc: 'View resume, private info, and documents.',
      icon: '👤',
      path: `/employees/${user?.id}`,
      color: 'from-blue-500/10 to-indigo-500/10 hover:border-blue-500',
    },
    {
      title: 'Attendance',
      desc: 'Check monthly records and work hours.',
      icon: '📅',
      path: '/attendance',
      color: 'from-green-500/10 to-emerald-500/10 hover:border-green-500',
    },
    {
      title: 'Leave Requests',
      desc: 'Apply for time off and check balances.',
      icon: '✈️',
      path: '/time-off',
      color: 'from-purple-500/10 to-pink-500/10 hover:border-purple-500',
    },
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white">
            Welcome back, {user?.first_name || 'Employee'}!
          </h1>
          <p className="text-gray-400 mt-1">Here is a quick overview of your workspace today.</p>
        </div>
        {status && (
          <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-xl px-5 py-3 shadow-md">
            <span className={`w-3.5 h-3.5 rounded-full ${status.checked_in ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-red-500 shadow-[0_0_10px_#ef4444]'}`} />
            <span className="text-sm font-semibold text-white">
              Status: {status.checked_in ? 'Checked In' : 'Checked Out'}
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((c) => (
          <button
            key={c.title}
            onClick={() => navigate(c.path)}
            className={`bg-gradient-to-br ${c.color} border border-gray-800 rounded-xl p-6 text-left hover:shadow-lg transition group flex flex-col justify-between h-44`}
          >
            <span className="text-3xl">{c.icon}</span>
            <div>
              <h3 className="text-lg font-bold text-white group-hover:text-purple-400 transition">
                {c.title}
              </h3>
              <p className="text-xs text-gray-500 mt-1">{c.desc}</p>
            </div>
          </button>
        ))}

        <button
          onClick={handleLogout}
          className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border border-gray-800 hover:border-red-500 rounded-xl p-6 text-left hover:shadow-lg transition group flex flex-col justify-between h-44"
        >
          <span className="text-3xl">🚪</span>
          <div>
            <h3 className="text-lg font-bold text-white group-hover:text-red-400 transition">
              Logout
            </h3>
            <p className="text-xs text-gray-500 mt-1">Sign out of your active session.</p>
          </div>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-base font-bold text-white mb-4">Recent Leaves / Activity</h2>
          {loading ? (
            <p className="text-sm text-gray-500">Loading activity...</p>
          ) : recentLeaves.length === 0 ? (
            <p className="text-sm text-gray-500">No recent time-off requests found.</p>
          ) : (
            <div className="space-y-4">
              {recentLeaves.map((l) => (
                <div key={l.id} className="flex justify-between items-center border-b border-gray-800 pb-3 last:border-0 last:pb-0">
                  <div>
                    <p className="text-sm font-semibold text-white">{l.leave_type}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {l.start_date} to {l.end_date}
                    </p>
                  </div>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                    l.status === 'Approved' ? 'bg-green-500/10 text-green-400' :
                    l.status === 'Rejected' ? 'bg-red-500/10 text-red-400' :
                    'bg-blue-500/10 text-blue-400'
                  }`}>
                    {l.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info alerts */}
        <div className="bg-gradient-to-br from-purple-900/10 to-indigo-900/10 border border-purple-500/20 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-2">💡 Quick Tips</h2>
            <p className="text-sm text-gray-400 leading-relaxed">
              Ensure you check in using the status dot at the top-right corner of the navigation bar when starting your work day. 
              Break hours are automatically deducted based on your defined salary structures.
            </p>
          </div>
          <p className="text-xs text-purple-400 font-medium mt-4">
            Need changes to private or bank info? Update them in "My Profile".
          </p>
        </div>
      </div>
    </div>
  );
}
