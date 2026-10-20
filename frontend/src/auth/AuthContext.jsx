import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { getCurrentUser, loginUser, logoutUser } from '../api/auth';
import { TOKEN_KEY } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const clearSession = useCallback(() => {
    window.localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    const onUnauthorized = () => setUser(null);
    window.addEventListener('taskflow:unauthorized', onUnauthorized);
    const token = window.localStorage.getItem(TOKEN_KEY);
    if (!token) setLoading(false);
    else getCurrentUser().then(setUser).catch(clearSession).finally(() => setLoading(false));
    return () => window.removeEventListener('taskflow:unauthorized', onUnauthorized);
  }, [clearSession]);

  const login = useCallback(async (credentials) => {
    const result = await loginUser(credentials);
    window.localStorage.setItem(TOKEN_KEY, result.access_token);
    setUser(result.user);
    return result.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      if (window.localStorage.getItem(TOKEN_KEY)) await logoutUser();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}