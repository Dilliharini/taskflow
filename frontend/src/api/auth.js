import apiClient from './client';

export async function registerUser(values) {
  const response = await apiClient.post('/api/v1/auth/register', values);
  return response.data;
}

export async function loginUser(values) {
  const response = await apiClient.post('/api/v1/auth/login', values);
  return response.data;
}

export async function getCurrentUser() {
  const response = await apiClient.get('/api/v1/auth/me');
  return response.data;
}

export async function logoutUser() {
  const response = await apiClient.post('/api/v1/auth/logout');
  return response.data;
}