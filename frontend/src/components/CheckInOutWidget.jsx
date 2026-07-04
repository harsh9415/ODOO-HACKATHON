import { useState, useEffect } from 'react';
import { attendanceApi } from '../api/client';

function formatTime(timeStr) {
  if (!timeStr) return '';
  const [h, m] = timeStr.split(':');
  const hour = parseInt(h, 10);
  const ampm = hour >= 12 ? 'PM' : 'AM';
  const h12 = hour % 12 || 12;
  return `${h12}:${m} ${ampm}`;
}

export default function CheckInOutWidget({ statusDot, setStatusDot, onClose }) {
  const [checkedIn, setCheckedIn] = useState(statusDot === 'green');
  const [checkInTime, setCheckInTime] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data } = await attendanceApi.todayStatus();
        setCheckedIn(data.checked_in);
        setCheckInTime(data.check_in_time);
        setStatusDot(data.status_dot);
      } catch {
        /* ignore */
      }
    };
    fetch();
  }, [setStatusDot]);

  const handleCheckIn = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await attendanceApi.checkIn();
      setCheckedIn(true);
      setCheckInTime(data.check_in);
      setStatusDot('green');
      window.dispatchEvent(new Event('attendance-update'));
    } catch (err) {
      setError(err.response?.data?.detail || 'Check-in failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckOut = async () => {
    setLoading(true);
    setError('');
    try {
      await attendanceApi.checkOut();
      setCheckedIn(false);
      setCheckInTime(null);
      setStatusDot('red');
      window.dispatchEvent(new Event('attendance-update'));
      onClose?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Check-out failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute right-0 top-full mt-2 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-4 z-50">
      {error && <p className="text-red-400 text-xs mb-2">{error}</p>}
      {!checkedIn ? (
        <button
          onClick={handleCheckIn}
          disabled={loading}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          Check In →
        </button>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-300">
            Since <span className="text-white font-medium">{formatTime(checkInTime)}</span>
          </p>
          <button
            onClick={handleCheckOut}
            disabled={loading}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg text-sm font-medium disabled:opacity-50"
          >
            Check Out →
          </button>
        </div>
      )}
    </div>
  );
}
