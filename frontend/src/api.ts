import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Polyfill for file uploads
export const uploadStatement = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
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
