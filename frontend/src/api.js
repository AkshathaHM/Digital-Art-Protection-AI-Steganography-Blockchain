import axios from 'axios';

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000' });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('dap_access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('dap_access_token');
      localStorage.removeItem('dap_user');
      if (window.location.pathname !== '/login') window.location.assign('/login');
    }
    return Promise.reject(error);
  },
);

export async function login(credentials) {
  const { data } = await api.post('/api/auth/login', credentials);
  localStorage.setItem('dap_access_token', data.access_token);
  localStorage.setItem('dap_user', JSON.stringify(data.user));
  return data.user;
}

export async function register(details) {
  const endpoint = details.role === 'buyer' ? '/api/auth/register/buyer' : '/api/auth/register/artist';
  const { role, ...credentials } = details;
  const { data } = await api.post(endpoint, credentials);
  return data;
}

export async function requestPasswordReset(email) {
  const { data } = await api.post('/api/auth/forgot-password', { email });
  return data;
}

export async function resetPassword(token, password) {
  const { data } = await api.post('/api/auth/reset-password', { token, password });
  return data;
}

export async function uploadArtwork(formData, onUploadProgress) {
  const { data } = await api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  });
  return data;
}

export async function getGallery() {
  const { data } = await api.get('/api/gallery');
  return data;
}

export async function getMyArtworks() {
  const { data } = await api.get('/api/my-artworks');
  return data;
}

export async function getMyPurchases() {
  const { data } = await api.get('/api/my-purchases');
  return data;
}

export async function getRecommendations(params) {
  const { data } = await api.get('/api/recommendations', { params });
  return data;
}

export async function verifyOwnership(payload) {
  const { data } = await api.post('/api/verify-ownership', payload);
  return data;
}

export async function purchaseArtwork(payload) {
  const { data } = await api.post('/api/purchase', payload);
  return data;
}

export async function downloadOriginal(artworkId) {
  const response = await api.get(`/api/artworks/${encodeURIComponent(artworkId)}/download`, { responseType: 'blob' });
  return response.data;
}

export async function getAdminUsers() {
  const { data } = await api.get('/api/admin/users');
  return data;
}

export async function getAdminArtworks() {
  const { data } = await api.get('/api/admin/artworks');
  return data;
}

export async function updateAdminUser(id, payload) {
  const { data } = await api.patch(`/api/admin/users/${id}`, payload);
  return data;
}

export async function deleteAdminArtwork(id) {
  const { data } = await api.delete(`/api/admin/artworks/${id}`);
  return data;
}
