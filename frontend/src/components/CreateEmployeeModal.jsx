import { useState } from 'react';
import { employeesApi } from '../api/client';

export default function CreateEmployeeModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    location: 'Bangalore',
    date_of_joining: new Date().toISOString().split('T')[0],
    company_id: 1,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { data } = await employeesApi.create(form);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create employee');
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-8 max-w-md w-full">
          <h2 className="text-xl font-bold text-green-400 mb-4">Employee Created!</h2>
          <div className="space-y-2 text-sm">
            <p><span className="text-gray-500">Name:</span> {result.first_name} {result.last_name}</p>
            <p><span className="text-gray-500">Login ID:</span> <code className="text-purple-400">{result.login_id}</code></p>
            <p><span className="text-gray-500">Temp Password:</span> <code className="text-yellow-400">{result.temporary_password}</code></p>
          </div>
          <p className="text-xs text-gray-500 mt-4">Share these credentials securely with the employee.</p>
          <button
            onClick={onCreated}
            className="mt-6 w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg"
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-8 max-w-lg w-full my-8">
        <h2 className="text-xl font-bold text-white mb-6">Create New Employee</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">First Name</label>
              <input name="first_name" value={form.first_name} onChange={handleChange} required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Last Name</label>
              <input name="last_name" value={form.last_name} onChange={handleChange} required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Phone</label>
              <input name="phone" value={form.phone} onChange={handleChange}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Department</label>
              <input name="department" value={form.department} onChange={handleChange}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Location</label>
              <input name="location" value={form.location} onChange={handleChange}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Date of Joining</label>
              <input name="date_of_joining" type="date" value={form.date_of_joining} onChange={handleChange} required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm" />
            </div>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={loading}
              className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-medium disabled:opacity-50">
              {loading ? 'Creating...' : 'Sign Up'}
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
