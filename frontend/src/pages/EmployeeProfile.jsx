import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { employeesApi, authApi, uploadsApi } from '../api/client';

const TABS = ['Resume', 'Private Info', 'Salary Info', 'Documents', 'Security'];

export default function EmployeeProfile() {
  const { userId } = useParams();
  const { user, isAdmin } = useAuth();
  const targetId = parseInt(userId, 10);
  const isSelf = user?.id === targetId;
  const canEdit = isAdmin || isSelf;
  const viewOnly = !isAdmin && !isSelf;

  const [tab, setTab] = useState('Resume');
  const [header, setHeader] = useState(null);
  const [resume, setResume] = useState(null);
  const [privateInfo, setPrivateInfo] = useState(null);
  const [salary, setSalary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [privRes, resumeRes] = await Promise.all([
          employeesApi.getPrivateInfo(targetId),
          employeesApi.getResume(targetId),
        ]);
        setPrivateInfo(privRes.data);
        setHeader(privRes.data.header);
        setResume(resumeRes.data);
        if (isAdmin || isSelf) {
          try {
            const salRes = await employeesApi.getSalary(targetId);
            setSalary(salRes.data);
          } catch {
            /* salary may not exist */
          }
        }
      } catch {
        setError('Failed to load profile');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [targetId, isAdmin, isSelf]);

  const visibleTabs = TABS.filter((t) => {
    if (t === 'Salary Info') return isAdmin || isSelf;
    if (t === 'Security') return isSelf;
    return true;
  });

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {header && (
        <div className="flex items-start gap-6 mb-8">
          <div className="w-24 h-24 rounded-full bg-gray-800 flex items-center justify-center text-3xl font-bold text-purple-400">
            {header.first_name[0]}{header.last_name[0]}
          </div>
          <div>
            <h1 className="text-2xl font-bold">{header.first_name} {header.last_name}</h1>
            <div className="grid grid-cols-2 gap-x-8 gap-y-1 mt-3 text-sm">
              <p><span className="text-gray-500">Login ID:</span> {header.login_id}</p>
              <p><span className="text-gray-500">Email:</span> {header.email}</p>
              <p><span className="text-gray-500">Mobile:</span> {header.phone || '—'}</p>
              <p><span className="text-gray-500">Department:</span> {header.department || '—'}</p>
              <p><span className="text-gray-500">Manager:</span> {header.manager_name || '—'}</p>
              <p><span className="text-gray-500">Location:</span> {header.location || '—'}</p>
            </div>
          </div>
        </div>
      )}

      {viewOnly && (
        <p className="text-xs text-gray-500 mb-4 bg-gray-900 border border-gray-800 rounded-lg px-4 py-2">
          View-only mode
        </p>
      )}

      <div className="flex gap-1 mb-6 border-b border-gray-800">
        {visibleTabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
              tab === t ? 'border-purple-500 text-purple-400' : 'border-transparent text-gray-500 hover:text-white'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {message && <p className="text-green-400 text-sm mb-4">{message}</p>}
      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      {tab === 'Resume' && (
        <ResumeTab
          resume={resume}
          canEdit={canEdit && !viewOnly}
          onSave={async (data) => {
            setSaving(true);
            setMessage('');
            try {
              const { data: updated } = await employeesApi.updateResume(targetId, data);
              setResume(updated);
              setMessage('Resume saved');
            } catch (err) {
              setError(err.response?.data?.detail || 'Save failed');
            } finally {
              setSaving(false);
            }
          }}
          saving={saving}
        />
      )}

      {tab === 'Private Info' && privateInfo && (
        <PrivateInfoTab
          info={privateInfo}
          canEdit={canEdit && !viewOnly}
          isAdmin={isAdmin}
          onSave={async (data) => {
            setSaving(true);
            setMessage('');
            try {
              const { data: updated } = await employeesApi.updatePrivateInfo(targetId, data);
              setPrivateInfo(updated);
              setHeader(updated.header);
              setMessage('Private info saved');
            } catch (err) {
              setError(err.response?.data?.detail || 'Save failed');
            } finally {
              setSaving(false);
            }
          }}
          saving={saving}
        />
      )}

      {tab === 'Salary Info' && salary && (
        <SalaryTab
          salary={salary}
          canEdit={isAdmin}
          onSave={async (data) => {
            setSaving(true);
            setMessage('');
            try {
              const { data: updated } = await employeesApi.updateSalary(targetId, data);
              setSalary(updated);
              setMessage('Salary updated');
            } catch (err) {
              setError(err.response?.data?.detail || 'Save failed');
            } finally {
              setSaving(false);
            }
          }}
          saving={saving}
        />
      )}

      {tab === 'Documents' && (
        <DocumentsTab
          userId={targetId}
          canEdit={canEdit && !viewOnly}
        />
      )}

      {tab === 'Security' && isSelf && <SecurityTab />}
    </div>
  );
}

function ResumeTab({ resume, canEdit, onSave, saving }) {
  const [form, setForm] = useState(resume || {});
  const [skillInput, setSkillInput] = useState('');
  const [certInput, setCertInput] = useState('');

  useEffect(() => { setForm(resume || {}); }, [resume]);

  const addSkill = () => {
    if (!skillInput.trim()) return;
    setForm({ ...form, skills: [...(form.skills || []), skillInput.trim()] });
    setSkillInput('');
  };

  const addCert = () => {
    if (!certInput.trim()) return;
    setForm({ ...form, certifications: [...(form.certifications || []), certInput.trim()] });
    setCertInput('');
  };

  return (
    <div className="space-y-4">
      {['about', 'job_love_note', 'interests'].map((field) => (
        <div key={field}>
          <label className="block text-sm text-gray-400 mb-1 capitalize">{field.replace(/_/g, ' ')}</label>
          <textarea
            value={form[field] || ''}
            onChange={(e) => setForm({ ...form, [field]: e.target.value })}
            disabled={!canEdit}
            rows={3}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-2 text-sm disabled:opacity-70"
          />
        </div>
      ))}
      <div>
        <label className="block text-sm text-gray-400 mb-2">Skills</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {(form.skills || []).map((s, i) => (
            <span key={i} className="bg-purple-900/50 text-purple-300 px-3 py-1 rounded-full text-xs flex items-center gap-1">
              {s}
              {canEdit && (
                <button onClick={() => setForm({ ...form, skills: form.skills.filter((_, j) => j !== i) })} className="text-red-400">×</button>
              )}
            </span>
          ))}
        </div>
        {canEdit && (
          <div className="flex gap-2">
            <input value={skillInput} onChange={(e) => setSkillInput(e.target.value)}
              className="flex-1 bg-gray-900 border border-gray-800 rounded-lg px-3 py-1.5 text-sm" placeholder="Add skill" />
            <button onClick={addSkill} className="text-purple-400 text-sm">+ add</button>
          </div>
        )}
      </div>
      <div>
        <label className="block text-sm text-gray-400 mb-2">Certifications</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {(form.certifications || []).map((c, i) => (
            <span key={i} className="bg-gray-800 text-gray-300 px-3 py-1 rounded-full text-xs flex items-center gap-1">
              {c}
              {canEdit && (
                <button onClick={() => setForm({ ...form, certifications: form.certifications.filter((_, j) => j !== i) })} className="text-red-400">×</button>
              )}
            </span>
          ))}
        </div>
        {canEdit && (
          <div className="flex gap-2">
            <input value={certInput} onChange={(e) => setCertInput(e.target.value)}
              className="flex-1 bg-gray-900 border border-gray-800 rounded-lg px-3 py-1.5 text-sm" placeholder="Add certification" />
            <button onClick={addCert} className="text-purple-400 text-sm">+ add</button>
          </div>
        )}
      </div>
      {canEdit && (
        <button onClick={() => onSave(form)} disabled={saving}
          className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg text-sm disabled:opacity-50">
          {saving ? 'Saving...' : 'Save'}
        </button>
      )}
    </div>
  );
}

function PrivateInfoTab({ info, canEdit, isAdmin, onSave, saving }) {
  const [form, setForm] = useState({
    ...info,
    bank_details: info.bank_details || {},
  });

  useEffect(() => { setForm({ ...info, bank_details: info.bank_details || {} }); }, [info]);

  const setField = (field, value) => setForm({ ...form, [field]: value });
  const setBank = (field, value) => setForm({ ...form, bank_details: { ...form.bank_details, [field]: value } });

  const fields = [
    ['dob', 'date'], ['residing_address', 'text'], ['nationality', 'text'],
    ['personal_email', 'email'], ['gender', 'text'], ['marital_status', 'text'],
    ['date_of_joining', 'date'], ['phone', 'text'], ['emp_code', 'text'],
  ];
  const adminFields = [['department', 'text'], ['location', 'text']];
  const bankFields = ['account_number', 'bank_name', 'ifsc_code', 'pan_no', 'uan_no'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">Personal Details</h3>
        {fields.map(([f, type]) => (
          <div key={f}>
            <label className="block text-xs text-gray-500 mb-1 capitalize">{f.replace(/_/g, ' ')}</label>
            <input type={type} value={form[f] || ''}
              onChange={(e) => setField(f, e.target.value)}
              disabled={!canEdit || (!['residing_address', 'phone'].includes(f) && !isAdmin)}
              className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm disabled:opacity-70" />
          </div>
        ))}
        {isAdmin && adminFields.map(([f]) => (
          <div key={f}>
            <label className="block text-xs text-gray-500 mb-1 capitalize">{f}</label>
            <input value={form[f] || ''} onChange={(e) => setField(f, e.target.value)}
              className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm" />
          </div>
        ))}
      </div>
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">Bank Details</h3>
        {bankFields.map((f) => (
          <div key={f}>
            <label className="block text-xs text-gray-500 mb-1 uppercase">{f.replace(/_/g, ' ')}</label>
            <input value={form.bank_details?.[f] || ''} onChange={(e) => setBank(f, e.target.value)}
              disabled={!canEdit || !isAdmin}
              className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm disabled:opacity-70" />
          </div>
        ))}
      </div>
      {canEdit && (
        <div className="md:col-span-2">
          <button onClick={() => onSave({
            dob: form.dob || null,
            residing_address: form.residing_address,
            nationality: form.nationality,
            personal_email: form.personal_email,
            gender: form.gender,
            marital_status: form.marital_status,
            date_of_joining: form.date_of_joining || null,
            phone: form.phone,
            department: form.department,
            location: form.location,
            emp_code: form.emp_code,
            bank_details: form.bank_details,
          })} disabled={saving}
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg text-sm disabled:opacity-50">
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      )}
    </div>
  );
}

function SalaryTab({ salary, canEdit, onSave, saving }) {
  const [form, setForm] = useState({
    month_wage: salary.month_wage,
    working_days_per_week: salary.working_days_per_week,
    break_time_minutes: salary.break_time_hours * 60,
    basic_pct: salary.basic_pct,
    hra_pct: salary.hra_pct,
    standard_allowance_pct: salary.standard_allowance_pct,
    performance_bonus_pct: salary.performance_bonus_pct,
    lta_pct: salary.lta_pct,
    pf_employee_pct: salary.pf_employee_pct,
    pf_employer_pct: salary.pf_employer_pct,
    professional_tax: salary.professional_tax,
  });

  const wage = parseFloat(form.month_wage) || 0;
  const basic = wage * (form.basic_pct / 100);
  const hra = basic * (form.hra_pct / 100);
  const std = wage * (form.standard_allowance_pct / 100);
  const perf = wage * (form.performance_bonus_pct / 100);
  const lta = wage * (form.lta_pct / 100);
  const fixed = Math.max(0, wage - basic - hra - std - perf - lta);
  const pfEmp = basic * (form.pf_employee_pct / 100);
  const pfEr = basic * (form.pf_employer_pct / 100);
  const net = wage - pfEmp - form.professional_tax;

  const components = [
    { name: 'Basic Salary', pct: form.basic_pct, amount: basic, base: 'Wage' },
    { name: 'HRA', pct: form.hra_pct, amount: hra, base: 'Basic' },
    { name: 'Standard Allowance', pct: form.standard_allowance_pct, amount: std, base: 'Wage' },
    { name: 'Performance Bonus', pct: form.performance_bonus_pct, amount: perf, base: 'Wage' },
    { name: 'LTA', pct: form.lta_pct, amount: lta, base: 'Wage' },
    { name: 'Fixed Allowance', pct: 0, amount: fixed, base: 'Remainder' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="text-xs text-gray-500">Monthly Wage (₹)</label>
          <input type="number" value={form.month_wage}
            onChange={(e) => setForm({ ...form, month_wage: parseFloat(e.target.value) })}
            disabled={!canEdit}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm mt-1 disabled:opacity-70" />
        </div>
        <div>
          <label className="text-xs text-gray-500">Yearly Wage (₹)</label>
          <p className="text-lg font-semibold mt-1">₹{(wage * 12).toLocaleString()}</p>
        </div>
        <div>
          <label className="text-xs text-gray-500">Working Days/Week</label>
          <input type="number" value={form.working_days_per_week}
            onChange={(e) => setForm({ ...form, working_days_per_week: parseInt(e.target.value, 10) })}
            disabled={!canEdit}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm mt-1 disabled:opacity-70" />
        </div>
        <div>
          <label className="text-xs text-gray-500">Break Time (hrs)</label>
          <input type="number" step="0.5" value={form.break_time_minutes / 60}
            onChange={(e) => setForm({ ...form, break_time_minutes: parseFloat(e.target.value) * 60 })}
            disabled={!canEdit}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm mt-1 disabled:opacity-70" />
        </div>
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-500 border-b border-gray-800">
            <th className="text-left py-2">Component</th>
            <th className="text-right py-2">%</th>
            <th className="text-right py-2">Amount/mo (₹)</th>
          </tr>
        </thead>
        <tbody>
          {components.map((c) => (
            <tr key={c.name} className="border-b border-gray-900">
              <td className="py-2">{c.name} <span className="text-xs text-gray-600">({c.base})</span></td>
              <td className="text-right">
                {c.name !== 'Fixed Allowance' && canEdit ? (
                  <input type="number" step="0.01" value={form[c.name === 'Basic Salary' ? 'basic_pct' : c.name === 'HRA' ? 'hra_pct' : c.name === 'Standard Allowance' ? 'standard_allowance_pct' : c.name === 'Performance Bonus' ? 'performance_bonus_pct' : 'lta_pct']}
                    onChange={(e) => {
                      const key = c.name === 'Basic Salary' ? 'basic_pct' : c.name === 'HRA' ? 'hra_pct' : c.name === 'Standard Allowance' ? 'standard_allowance_pct' : c.name === 'Performance Bonus' ? 'performance_bonus_pct' : 'lta_pct';
                      setForm({ ...form, [key]: parseFloat(e.target.value) });
                    }}
                    className="w-20 bg-gray-900 border border-gray-800 rounded px-2 py-1 text-right text-sm" />
                ) : (
                  c.pct ? `${c.pct}%` : '—'
                )}
              </td>
              <td className="text-right py-2">₹{c.amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="bg-gray-900 rounded-lg p-4">
          <p className="text-gray-500 mb-2">PF Contribution</p>
          <p>Employee: ₹{pfEmp.toFixed(0)} ({form.pf_employee_pct}% of Basic)</p>
          <p>Employer: ₹{pfEr.toFixed(0)} ({form.pf_employer_pct}% of Basic)</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-4">
          <p className="text-gray-500 mb-2">Deductions</p>
          <p>Professional Tax: ₹{form.professional_tax}</p>
          <p className="font-semibold text-green-400 mt-2">Net Take-Home: ₹{net.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
        </div>
      </div>

      {canEdit && (
        <button onClick={() => onSave(form)} disabled={saving}
          className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg text-sm disabled:opacity-50">
          {saving ? 'Saving...' : 'Save Salary'}
        </button>
      )}
    </div>
  );
}

function SecurityTab() {
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg('');
    setErr('');
    try {
      await authApi.changePassword(form);
      setMsg('Password changed successfully');
      setForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      setErr(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md space-y-4">
      {['current_password', 'new_password', 'confirm_password'].map((f) => (
        <div key={f}>
          <label className="block text-sm text-gray-400 mb-1 capitalize">{f.replace(/_/g, ' ')}</label>
          <input type="password" value={form[f]}
            onChange={(e) => setForm({ ...form, [f]: e.target.value })}
            required minLength={f !== 'current_password' ? 8 : undefined}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-2 text-sm" />
        </div>
      ))}
      {msg && <p className="text-green-400 text-sm">{msg}</p>}
      {err && <p className="text-red-400 text-sm">{err}</p>}
      <button type="submit" disabled={loading}
        className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg text-sm disabled:opacity-50">
        {loading ? 'Changing...' : 'Change Password'}
      </button>
    </form>
  );
}

function DocumentsTab({ userId, canEdit }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const { data } = await employeesApi.getDocuments(userId);
      setDocs(data);
    } catch {
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, [userId]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const docName = name.trim() || file.name;
    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const { data: uploadRes } = await uploadsApi.file(formData);
      await employeesApi.uploadDocument(userId, {
        name: docName,
        file_url: uploadRes.url,
        file_type: file.type || null,
      });
      setName('');
      fetchDocs();
    } catch {
      setError('Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await employeesApi.deleteDocument(userId, docId);
      fetchDocs();
    } catch {
      setError('Failed to delete document');
    }
  };

  if (loading) {
    return <div className="text-gray-500 text-sm">Loading documents...</div>;
  }

  return (
    <div className="space-y-6">
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {canEdit && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white">Upload New Document</h3>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="text-xs text-gray-500 block mb-1">Document Name (Optional)</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Aadhaar Card, Passport"
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <input
                type="file"
                id="doc-file-upload"
                className="hidden"
                onChange={handleFileUpload}
              />
              <label
                htmlFor="doc-file-upload"
                className="cursor-pointer inline-block bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition"
              >
                {uploading ? 'Uploading...' : 'Choose File & Upload'}
              </label>
            </div>
          </div>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4">Employee Documents</h3>
        {docs.length === 0 ? (
          <p className="text-sm text-gray-500">No documents uploaded yet.</p>
        ) : (
          <div className="divide-y divide-gray-800">
            {docs.map((doc) => (
              <div key={doc.id} className="py-3 flex items-center justify-between gap-4">
                <div>
                  <p className="font-semibold text-sm text-white">{doc.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Uploaded on {new Date(doc.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <a
                    href={doc.file_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-purple-400 hover:underline"
                  >
                    View / Download
                  </a>
                  {canEdit && (
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-xs text-red-400 hover:underline"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
