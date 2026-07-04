import { useState } from 'react';
import { Navigate, Outlet, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/client';
import TopNav from '../components/TopNav';

export default function ProtectedLayout() {
  const { user, loading } = useAuth();
  const [verifying, setVerifying] = useState(false);
  const [verifError, setVerifError] = useState('');
  const [verifSuccess, setVerifSuccess] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!user) return <Navigate to="/signin" replace />;

  if (!user.email_verified) {
    const handleVerify = async () => {
      setVerifying(true);
      setVerifError('');
      try {
        await authApi.verifyEmail();
        setVerifSuccess(true);
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } catch {
        setVerifError('Verification failed');
      } finally {
        setVerifying(false);
      }
    };

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
        <div className="max-w-md w-full bg-gray-900 border border-gray-800 rounded-xl p-8 text-center space-y-6">
          <div className="w-16 h-16 bg-purple-600/10 border border-purple-500 rounded-full flex items-center justify-center mx-auto text-2xl">
            📧
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Verify your Email</h2>
            <p className="text-gray-400 text-sm mt-2">
              A verification email has been simulated for <span className="text-white font-medium">{user.email}</span>.
              Please click below to complete the verification.
            </p>
          </div>
          {verifError && <p className="text-red-400 text-sm">{verifError}</p>}
          {verifSuccess && <p className="text-green-400 text-sm">✓ Email verified successfully! Reloading...</p>}
          <button
            onClick={handleVerify}
            disabled={verifying || verifSuccess}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2.5 rounded-lg transition disabled:opacity-50"
          >
            {verifying ? 'Verifying...' : 'VERIFY EMAIL'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <TopNav />
      {user?.must_change_password && (
        <div className="bg-yellow-900/40 border-b border-yellow-700 px-6 py-3 text-sm text-yellow-200">
          Please change your temporary password from{' '}
          <Link to={`/employees/${user.id}`} className="underline font-medium text-yellow-100">
            My Profile → Security
          </Link>
          .
        </div>
      )}
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  );
}
