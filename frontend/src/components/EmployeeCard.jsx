import { useNavigate } from 'react-router-dom';

function StatusIcon({ status }) {
  if (status === 'present') {
    return <span className="w-3 h-3 rounded-full bg-green-500 block" title="Present" />;
  }
  if (status === 'leave') {
    return <span className="text-sm" title="On Leave">✈️</span>;
  }
  return <span className="w-3 h-3 rounded-full bg-yellow-500 block" title="Absent" />;
}

export default function EmployeeCard({ employee }) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(`/employees/${employee.user_id}`)}
      className="relative bg-gray-900 border border-gray-800 rounded-xl p-6 flex flex-col items-center gap-3 hover:border-purple-500 hover:shadow-lg hover:shadow-purple-500/10 transition text-left w-full"
    >
      <div className="absolute top-3 right-3">
        <StatusIcon status={employee.status_icon} />
      </div>
      <div className="w-20 h-20 rounded-full bg-gray-800 flex items-center justify-center overflow-hidden">
        {employee.profile_picture_url ? (
          <img src={employee.profile_picture_url} alt="" className="w-full h-full object-cover" />
        ) : (
          <span className="text-2xl font-bold text-purple-400">
            {employee.first_name[0]}{employee.last_name[0]}
          </span>
        )}
      </div>
      <div className="text-center">
        <p className="font-semibold text-white">{employee.full_name}</p>
        {employee.department && (
          <p className="text-xs text-gray-500 mt-1">{employee.department}</p>
        )}
      </div>
    </button>
  );
}
