import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AvatarDropdown() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const initials = `${user?.first_name?.[0] || ''}${user?.last_name?.[0] || ''}`;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="w-9 h-9 rounded-full bg-purple-600 flex items-center justify-center text-sm font-bold hover:ring-2 ring-purple-400 transition"
      >
        {user?.profile_picture_url ? (
          <img src={user.profile_picture_url} alt="" className="w-full h-full rounded-full object-cover" />
        ) : (
          initials || '?'
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
          <button
            onClick={() => {
              navigate(`/employees/${user.id}`);
              setOpen(false);
            }}
            className="w-full text-left px-4 py-3 text-sm hover:bg-gray-700 rounded-t-lg"
          >
            My Profile
          </button>
          <button
            onClick={() => {
              logout();
              navigate('/signin');
            }}
            className="w-full text-left px-4 py-3 text-sm hover:bg-gray-700 text-red-400 rounded-b-lg"
          >
            Log Out
          </button>
        </div>
      )}
    </div>
  );
}
