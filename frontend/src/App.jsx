import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedLayout from './routes/ProtectedLayout';
import SignIn from './pages/SignIn';
import SignUpInfo from './pages/SignUpInfo';
import EmployeeList from './pages/EmployeeList';
import EmployeeDashboard from './pages/EmployeeDashboard';
import EmployeeProfile from './pages/EmployeeProfile';
import Attendance from './pages/Attendance';
import TimeOff from './pages/TimeOff';

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/" replace />;
  return children;
}

function DashboardSwitcher() {
  const { isAdmin, loading } = useAuth();
  if (loading) return null;
  return isAdmin ? <EmployeeList /> : <EmployeeDashboard />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/signin" element={<PublicRoute><SignIn /></PublicRoute>} />
          <Route path="/signup-info" element={<SignUpInfo />} />
          <Route element={<ProtectedLayout />}>
            <Route index element={<DashboardSwitcher />} />
            <Route path="employees/:userId" element={<EmployeeProfile />} />
            <Route path="attendance" element={<Attendance />} />
            <Route path="time-off" element={<TimeOff />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
