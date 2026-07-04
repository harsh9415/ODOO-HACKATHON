import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { attendanceApi } from '../api/client';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatTime(t) {
  if (!t) return '—';
  const [h, m] = t.split(':');
  const hour = parseInt(h, 10);
  const ampm = hour >= 12 ? 'PM' : 'AM';
  return `${hour % 12 || 12}:${m} ${ampm}`;
}

function formatHours(h) {
  const hrs = Math.floor(h);
  const mins = Math.round((h - hrs) * 60);
  return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
}

function AttendanceStatusBadge({ status }) {
  const styles = {
    present: 'bg-green-500/10 text-green-400 border-green-500/20',
    absent: 'bg-red-500/10 text-red-400 border-red-500/20',
    'half-day': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    leave: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  };
  
  const labels = {
    present: 'Present',
    absent: 'Absent',
    'half-day': 'Half-day',
    leave: 'Leave',
  };

  const currentStyle = styles[status] || 'bg-gray-500/10 text-gray-400 border-gray-500/20';
  const label = labels[status] || status;

  return (
    <span className={`inline-block px-2.5 py-1 text-xs font-semibold rounded-full border ${currentStyle} capitalize`}>
      {label}
    </span>
  );
}

export default function Attendance() {
  const { isAdmin } = useAuth();
  const today = new Date();

  if (isAdmin) return <AdminAttendanceView today={today} />;
  return <EmployeeAttendanceView today={today} />;
}

function EmployeeAttendanceView({ today }) {
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const { data: d } = await attendanceApi.myMonth(year, month);
        setData(d);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    fetch();

    window.addEventListener('attendance-update', fetch);
    return () => window.removeEventListener('attendance-update', fetch);
  }, [year, month]);

  const prev = () => {
    if (month === 1) { setYear(year - 1); setMonth(12); }
    else setMonth(month - 1);
  };
  const next = () => {
    if (month === 12) { setYear(year + 1); setMonth(1); }
    else setMonth(month + 1);
  };

  return (
    <div>
      <h1 className="text-xl font-bold mb-6">Attendance</h1>
      <div className="flex items-center gap-4 mb-6 flex-wrap">
        <button onClick={prev} className="text-gray-400 hover:text-white px-2">←</button>
        <span className="font-medium">{MONTHS[month - 1]} {year}</span>
        <button onClick={next} className="text-gray-400 hover:text-white px-2">→</button>
        {data && (
          <div className="flex gap-3 ml-auto flex-wrap">
            <Chip label="Days Present" value={data.days_present} />
            <Chip label="Leaves" value={data.leaves_count} />
            <Chip label="Working Days" value={data.total_working_days} />
          </div>
        )}
      </div>

      {loading ? <Spinner /> : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800">
              <th className="text-left py-3">Date</th>
              <th className="text-left py-3">Check In</th>
              <th className="text-left py-3">Check Out</th>
              <th className="text-left py-3">Work Hours</th>
              <th className="text-left py-3">Extra Hours</th>
              <th className="text-left py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.records.map((r) => (
              <tr key={r.date} className="border-b border-gray-900">
                <td className="py-2">{new Date(r.date + 'T00:00:00').toLocaleDateString()}</td>
                <td>{formatTime(r.check_in)}</td>
                <td>{formatTime(r.check_out)}</td>
                <td>{formatHours(r.work_hours)}</td>
                <td>{formatHours(r.extra_hours)}</td>
                <td className="py-2">
                  <AttendanceStatusBadge status={r.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function AdminAttendanceView({ today }) {
  const [date, setDate] = useState(today.toISOString().split('T')[0]);
  const [search, setSearch] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const { data: d } = await attendanceApi.adminDay(date, search || undefined);
        setData(d);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    fetch();

    window.addEventListener('attendance-update', fetch);
    return () => window.removeEventListener('attendance-update', fetch);
  }, [date, search]);

  const shiftDate = (days) => {
    const d = new Date(date);
    d.setDate(d.getDate() + days);
    setDate(d.toISOString().split('T')[0]);
  };

  return (
    <div>
      <h1 className="text-xl font-bold mb-6">Attendance</h1>
      <div className="flex items-center gap-4 mb-6 flex-wrap">
        <button onClick={() => shiftDate(-1)} className="text-gray-400 hover:text-white px-2">←</button>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
          className="bg-gray-900 border border-gray-800 rounded-lg px-3 py-1.5 text-sm" />
        <button onClick={() => shiftDate(1)} className="text-gray-400 hover:text-white px-2">→</button>
        <input type="text" placeholder="Search employees..." value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="ml-auto bg-gray-900 border border-gray-800 rounded-lg px-4 py-1.5 text-sm w-64" />
      </div>

      {loading ? <Spinner /> : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800">
              <th className="text-left py-3">Employee</th>
              <th className="text-left py-3">Check In</th>
              <th className="text-left py-3">Check Out</th>
              <th className="text-left py-3">Work Hours</th>
              <th className="text-left py-3">Extra Hours</th>
              <th className="text-left py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.records.map((r) => (
              <tr key={r.user_id} className="border-b border-gray-900">
                <td className="py-2">{r.employee_name}</td>
                <td>{r.check_in ? formatTime(r.check_in) : '—'}</td>
                <td>{r.check_out ? formatTime(r.check_out) : '—'}</td>
                <td>{formatHours(r.work_hours)}</td>
                <td>{formatHours(r.extra_hours)}</td>
                <td className="py-2">
                  <AttendanceStatusBadge status={r.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function Chip({ label, value }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-2 text-center min-w-[100px]">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex justify-center py-20">
      <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
    </div>
  );
}
