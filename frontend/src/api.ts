import axios from 'axios';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Inject Auth Token automatically into all outgoing API requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Expired or invalid token: clear the session so the login modal reappears.
// Only reload if a token was present (otherwise a guest's 401 would loop),
// and skip /auth/* so a wrong password shows its error instead of reloading.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthCall = (error.config?.url || '').startsWith('/auth/');
    if(error.response?.status === 401 && !isAuthCall && localStorage.getItem('auth_token')){
      //Token invalid or expired
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.reload();
    }
    return Promise.reject(error);
  }
)

// Polyfill for file uploads
export const uploadStatement = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = { 'Content-Type': 'multipart/form-data' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await axios.post(`${API_BASE}/upload`, formData, { headers });
  return response.data;
};

export const initiateBankSync = async (bankId: string, bankName: string, phoneNumber: string) => {
  const response = await api.post('/bank-sync/initiate', { bank_id: bankId, bank_name: bankName, phone_number: phoneNumber });
  return response.data;
};

export const verifyBankSyncOTP = async (sessionId: string, otp: string) => {
  const response = await api.post('/bank-sync/verify-otp', { session_id: sessionId, otp });
  return response.data;
};

export const triggerBankSync = async (sessionId: string) => {
  const response = await api.post('/bank-sync/sync', { session_id: sessionId });
  return response.data;
};

export const deleteTransaction = async (id: string) => {
  const response = await api.delete(`/analytics/transaction/${id}`);
  return response.data;
};

export const isDemoUser = () => {
  try{
    return JSON.parse(localStorage.getItem('auth_user') || 'null')?.user_id === 'demo_user';
  }catch{
    return false;
  }
};
