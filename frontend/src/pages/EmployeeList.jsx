import { useState, useEffect } from 'react';
import { employeesApi } from '../api/client';
import EmployeeCard from '../components/EmployeeCard';
import CreateEmployeeModal from '../components/CreateEmployeeModal';
import { useAuth } from '../context/AuthContext';

export default function EmployeeList() {
  const { isAdmin } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  const fetchEmployees = async (q) => {
    setLoading(true);
    setError('');
    try {
      const { data } = await employeesApi.list(q || undefined);
      setEmployees(data);
    } catch {
      setError('Failed to load employees');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees(search);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchEmployees(search);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        {isAdmin && (
          <button
            onClick={() => setShowCreate(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-5 py-2 rounded-lg font-semibold text-sm"
          >
            NEW
          </button>
        )}
        {!isAdmin && <div />}
        <form onSubmit={handleSearch} className="flex-1 max-w-md ml-auto">
          <input
            type="text"
            placeholder="Search employees..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
          />
        </form>
      </div>

      {error && <p className="text-red-400 mb-4">{error}</p>}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {employees.map((emp) => (
            <EmployeeCard key={emp.id} employee={emp} />
          ))}
        </div>
      )}

      {showCreate && (
        <CreateEmployeeModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            fetchEmployees(search);
          }}
        />
      )}
    </div>
  );
}
