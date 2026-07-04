import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.clear();
          window.location.href = '/signin';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

export const authApi = {
  login: (login_id, password) => api.post('/auth/login', { login_id, password }),
  me: () => api.get('/auth/me'),
  changePassword: (data) => api.post('/auth/change-password', data),
  register: (data) => api.post('/auth/register', data),
  verifyEmail: () => api.post('/auth/verify-email'),
};

export const employeesApi = {
  list: (search) => api.get('/employees', { params: { search } }),
  create: (data) => api.post('/employees', data),
  getResume: (userId) => api.get(`/employees/${userId}/resume`),
  updateResume: (userId, data) => api.put(`/employees/${userId}/resume`, data),
  getPrivateInfo: (userId) => api.get(`/employees/${userId}/private-info`),
  updatePrivateInfo: (userId, data) => api.put(`/employees/${userId}/private-info`, data),
  getSalary: (userId) => api.get(`/employees/${userId}/salary`),
  updateSalary: (userId, data) => api.put(`/employees/${userId}/salary`, data),
  getDocuments: (userId) => api.get(`/employees/${userId}/documents`),
  uploadDocument: (userId, data) => api.post(`/employees/${userId}/documents`, data),
  deleteDocument: (userId, docId) => api.delete(`/employees/${userId}/documents/${docId}`),
};

export const attendanceApi = {
  todayStatus: () => api.get('/attendance/today-status'),
  checkIn: () => api.post('/attendance/check-in'),
  checkOut: () => api.post('/attendance/check-out'),
  myMonth: (year, month) => api.get('/attendance/my-month', { params: { year, month } }),
  adminDay: (date, search) => api.get('/attendance/admin-day', { params: { date, search } }),
};

export const leaveApi = {
  balance: () => api.get('/leave/balance'),
  list: () => api.get('/leave'),
  apply: (data) => api.post('/leave', data),
  review: (id, data) => api.patch(`/leave/${id}/review`, data),
  calendar: (year) => api.get(`/leave/calendar/${year}`),
};

export const uploadsApi = {
  profilePicture: (formData) => api.post('/uploads/profile-picture', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  file: (formData) => api.post('/uploads/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
};
