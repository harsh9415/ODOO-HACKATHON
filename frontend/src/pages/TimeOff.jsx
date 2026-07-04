import { useState, useEffect, useMemo } from 'react';
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import enUS from 'date-fns/locale/en-US';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { useAuth } from '../context/AuthContext';
import { leaveApi, uploadsApi } from '../api/client';

const locales = { 'en-US': enUS };
const localizer = dateFnsLocalizer({ format, parse, startOfWeek, getDay, locales });

const LEAVE_TYPES = ['Paid Time Off', 'Sick Leave', 'Unpaid Leaves'];
const STATUS_COLORS = { Approved: '#22c55e', Rejected: '#ef4444', Pending: '#3b82f6' };

export default function TimeOff() {
  const { isAdmin } = useAuth();
  const [balance, setBalance] = useState(null);
  const [requests, setRequests] = useState([]);
  const [markers, setMarkers] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [year] = useState(new Date().getFullYear());

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [balRes, listRes, calRes] = await Promise.all([
        leaveApi.balance(),
        leaveApi.list(),
        leaveApi.calendar(year),
      ]);
      setBalance(balRes.data);
      setRequests(listRes.data);
      setMarkers(calRes.data);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, [year]);

  const events = useMemo(() =>
    requests.map((r) => ({
      id: r.id,
      title: `${r.leave_type} (${r.status})`,
      start: new Date(r.start_date + 'T00:00:00'),
      end: new Date(r.end_date + 'T23:59:59'),
      resource: r,
    })), [requests]);

  const eventStyle = (event) => ({
    style: {
      backgroundColor: STATUS_COLORS[event.resource.status] || '#6b7280',
      borderRadius: '4px',
      border: 'none',
      fontSize: '11px',
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Time Off</h1>
        {!isAdmin && (
          <button onClick={() => setShowModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-5 py-2 rounded-lg font-semibold text-sm">
            NEW
          </button>
        )}
      </div>

      {balance && (
        <div className="flex gap-4 mb-6 flex-wrap">
          <BalanceCard label="Paid time off" days={balance.paid_time_off} />
          <BalanceCard label="Sick time off" days={balance.sick_time_off} />
        </div>
      )}

      {isAdmin ? (
        <AdminLeaveList requests={requests} onReview={fetchAll} loading={loading} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-4 hrms-calendar">
            <Calendar
              localizer={localizer}
              events={events}
              startAccessor="start"
              endAccessor="end"
              style={{ height: 400 }}
              eventPropGetter={eventStyle}
              views={['month']}
              toolbar={false}
            />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Recent Activity</h3>
            <div className="space-y-2">
              {requests.slice(0, 8).map((r) => (
                <div key={r.id} className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 text-sm">
                  <p className="font-medium">{new Date(r.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</p>
                  <p className="text-gray-500">{r.leave_type}</p>
                  <StatusBadge status={r.status} />
                </div>
              ))}
            </div>
            <div className="mt-4 text-xs space-y-1">
              <p><span className="inline-block w-3 h-3 rounded-full bg-green-500 mr-2" />Approved</p>
              <p><span className="inline-block w-3 h-3 rounded-full bg-red-500 mr-2" />Rejected</p>
              <p><span className="inline-block w-3 h-3 rounded-full bg-blue-500 mr-2" />Pending</p>
            </div>
          </div>
        </div>
      )}

      {showModal && (
        <LeaveRequestModal
          onClose={() => setShowModal(false)}
          onSubmitted={() => { setShowModal(false); fetchAll(); }}
        />
      )}
    </div>
  );
}

function BalanceCard({ label, days }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl px-6 py-4 min-w-[180px]">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-2xl font-bold mt-1">{String(Math.floor(days)).padStart(2, '0')} <span className="text-sm font-normal text-gray-400">Days Available</span></p>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = { Approved: 'text-green-400', Rejected: 'text-red-400', Pending: 'text-blue-400' };
  return <span className={`text-xs ${colors[status] || 'text-gray-400'}`}>{status}</span>;
}

function AdminLeaveList({ requests, onReview, loading }) {
  const [reviewing, setReviewing] = useState(null);
  const [comment, setComment] = useState('');

  const handleReview = async (id, status) => {
    try {
      await leaveApi.review(id, { status, admin_comment: comment || null });
      setReviewing(null);
      setComment('');
      onReview();
    } catch {
      /* ignore */
    }
  };

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" /></div>;

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-gray-500 border-b border-gray-800">
          <th className="text-left py-3">Name</th>
          <th className="text-left py-3">Start Date</th>
          <th className="text-left py-3">End Date</th>
          <th className="text-left py-3">Type</th>
          <th className="text-left py-3">Status</th>
          <th className="text-left py-3">Actions</th>
        </tr>
      </thead>
      <tbody>
        {requests.map((r) => (
          <tr key={r.id} className="border-b border-gray-900">
            <td className="py-3">{r.employee_name}</td>
            <td>{r.start_date}</td>
            <td>{r.end_date}</td>
            <td>
              {r.leave_type}
              {r.attachment_url && (
                <a href={r.attachment_url} target="_blank" rel="noreferrer" className="ml-2 text-xs text-purple-400 underline hover:text-purple-300">
                  (View Attachment)
                </a>
              )}
            </td>
            <td><StatusBadge status={r.status} /></td>
            <td>
              {r.status === 'Pending' && (
                <div className="flex gap-2">
                  <button onClick={() => handleReview(r.id, 'Approved')}
                    className="w-7 h-7 bg-green-600 rounded hover:bg-green-700" title="Approve">✓</button>
                  <button onClick={() => { setReviewing(r.id); }}
                    className="w-7 h-7 bg-red-600 rounded hover:bg-red-700" title="Reject">✕</button>
                </div>
              )}
              {reviewing === r.id && (
                <div className="flex gap-2 mt-1">
                  <input value={comment} onChange={(e) => setComment(e.target.value)}
                    placeholder="Comment" className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs w-32" />
                  <button onClick={() => handleReview(r.id, 'Rejected')} className="text-xs text-red-400">Confirm</button>
                </div>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function LeaveRequestModal({ onClose, onSubmitted }) {
  const [form, setForm] = useState({
    leave_type: 'Paid Time Off',
    start_date: '',
    end_date: '',
    remarks: '',
    attachment_url: '',
  });
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const days = form.start_date && form.end_date
    ? Math.max(0, (new Date(form.end_date) - new Date(form.start_date)) / 86400000 + 1)
    : 0;

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const { data } = await uploadsApi.file(formData);
      setForm((f) => ({ ...f, attachment_url: data.url }));
    } catch {
      setError('File upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.leave_type === 'Sick Leave' && !form.attachment_url) {
      setError('Sick leave certificate is required');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await leaveApi.apply(form);
      onSubmitted();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-8 max-w-md w-full">
        <h2 className="text-xl font-bold mb-6">Request Time Off</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Time off Type</label>
            <select value={form.leave_type} onChange={(e) => setForm({ ...form, leave_type: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
              {LEAVE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">From</label>
              <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">To</label>
              <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Allocation</label>
            <p className="text-sm">{days.toFixed(2)} Days</p>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Attachment {form.leave_type === 'Sick Leave' && <span className="text-red-400 font-semibold">*</span>}
            </label>
            <input type="file" onChange={handleFileChange}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-400 file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700" />
            {uploading && <p className="text-xs text-gray-500 mt-1">Uploading...</p>}
            {form.attachment_url && (
              <p className="text-xs text-green-400 mt-1">
                ✓ Uploaded: <a href={form.attachment_url} target="_blank" rel="noreferrer" className="underline hover:text-green-300">View Attachment</a>
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Remarks</label>
            <textarea value={form.remarks} onChange={(e) => setForm({ ...form, remarks: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" rows={2} />
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex gap-3">
            <button type="submit" disabled={loading}
              className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg disabled:opacity-50">
              Submit
            </button>
            <button type="button" onClick={onClose}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg">
              Discard
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
