import apiClient from './client';

/**
 * Probes the backend system health and PostgreSQL database connectivity.
 * @param {boolean} strict - Whether to require database connectivity for 200 OK.
 * @returns {Promise<object>} Health response payload.
 */
export async function getSystemHealth(strict = false) {
  const response = await apiClient.get('/api/v1/health', {
    params: { strict },
  });
  return response.data;
}

/**
 * Rapid liveness probe.
 * @returns {Promise<object>} Ping response.
 */
export async function pingServer() {
  const response = await apiClient.get('/api/v1/ping');
  return response.data;
}
