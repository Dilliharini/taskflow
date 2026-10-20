import apiClient from './client';

const root = '/api/v1/projects';
const data = (promise) => promise.then((response) => response.data);

export const getDashboard = () => data(apiClient.get(`${root}/dashboard`));
export const listProjects = () => data(apiClient.get(root));
export const createProject = (payload) => data(apiClient.post(root, payload));
export const getProject = (id) => data(apiClient.get(`${root}/${id}`));
export const updateProject = (id, payload) => data(apiClient.patch(`${root}/${id}`, payload));
export const deleteProject = (id) => apiClient.delete(`${root}/${id}`);
export const listMembers = (id) => data(apiClient.get(`${root}/${id}/members`));
export const addMember = (id, payload) => data(apiClient.post(`${root}/${id}/members`, payload));
export const removeMember = (id, userId) => apiClient.delete(`${root}/${id}/members/${userId}`);
export const listTasks = (id, params = {}) => data(apiClient.get(`${root}/${id}/tasks`, { params }));
export const createTask = (id, payload) => data(apiClient.post(`${root}/${id}/tasks`, payload));
export const updateTask = (projectId, taskId, payload) => data(apiClient.patch(`${root}/${projectId}/tasks/${taskId}`, payload));
export const deleteTask = (projectId, taskId) => apiClient.delete(`${root}/${projectId}/tasks/${taskId}`);
export const listComments = (projectId, taskId) => data(apiClient.get(`${root}/${projectId}/tasks/${taskId}/comments`));
export const createComment = (projectId, taskId, payload) => data(apiClient.post(`${root}/${projectId}/tasks/${taskId}/comments`, payload));
export const updateComment = (projectId, taskId, commentId, payload) => data(apiClient.patch(`${root}/${projectId}/tasks/${taskId}/comments/${commentId}`, payload));
export const deleteComment = (projectId, taskId, commentId) => apiClient.delete(`${root}/${projectId}/tasks/${taskId}/comments/${commentId}`);
export const getActivity = (id) => data(apiClient.get(`${root}/${id}/activity`));