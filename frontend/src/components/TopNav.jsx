import { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { attendanceApi } from '../api/client';
import CheckInOutWidget from './CheckInOutWidget';
import AvatarDropdown from './AvatarDropdown';

export default function TopNav() {
  const { user } = useAuth();
  const location = useLocation();
  const [statusDot, setStatusDot] = useState('red');
  const [showWidget, setShowWidget] = useState(false);
  const widgetRef = useRef(null);

  const tabs = [
    { path: '/', label: 'Employees' },
    { path: '/attendance', label: 'Attendance' },
    { path: '/time-off', label: 'Time Off' },
  ];

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const { data } = await attendanceApi.todayStatus();
        setStatusDot(data.status_dot);
      } catch {
        setStatusDot('red');
      }
    };
    if (user) fetchStatus();
  }, [user, location.pathname]);

  useEffect(() => {
    const handleClick = (e) => {
      if (widgetRef.current && !widgetRef.current.contains(e.target)) {
        setShowWidget(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
      <div className="flex items-center gap-2 min-w-[120px]">
        {user?.company_logo_url ? (
          <img src={user.company_logo_url} alt="Logo" className="h-8 w-8 rounded" />
        ) : (
          <div className="h-8 w-8 rounded bg-purple-600 flex items-center justify-center text-xs font-bold">
            {user?.company_name?.split(' ').map((w) => w[0]).join('') || 'HR'}
          </div>
        )}
        <span className="text-sm font-semibold hidden sm:inline">{user?.company_name || 'HRMS'}</span>
      </div>

      <div className="flex gap-1">
        {tabs.map((tab) => (
          <Link
            key={tab.path}
            to={tab.path}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              location.pathname === tab.path || (tab.path !== '/' && location.pathname.startsWith(tab.path))
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            {tab.label}
          </Link>
        ))}
      </div>

      <div className="flex-1" />

      <div className="relative flex items-center gap-3" ref={widgetRef}>
        <button
          onClick={() => setShowWidget(!showWidget)}
          className="flex items-center gap-2 p-1 rounded-lg hover:bg-gray-800 transition"
        >
          <span
            className={`w-3 h-3 rounded-full ${statusDot === 'green' ? 'bg-green-500' : 'bg-red-500'}`}
          />
        </button>
        {showWidget && (
          <CheckInOutWidget
            statusDot={statusDot}
            setStatusDot={setStatusDot}
            onClose={() => setShowWidget(false)}
          />
        )}
        <AvatarDropdown />
      </div>
    </nav>
  );
}
