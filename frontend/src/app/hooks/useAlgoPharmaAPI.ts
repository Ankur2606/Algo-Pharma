import { useState, useCallback } from 'react';

const API_BASE_URL = '/api';

export interface AuthResponse {
  access_token: string;
  name: string;
  token_type: string;
  role: string;
}

export interface ChatResponse {
  ready: boolean;
  bot_message: string;
  state: Record<string, any>;
  project_id?: string;
}

export interface DashboardData {
  status: string;
  total_raw: number;
  processed: number;
  ae_flagged: number;
  sources: Record<string, number>;
  drug_counts: Record<string, number>;
  symptom_counts: Record<string, number>;
  sentiment_distribution: { positive: number; neutral: number; negative: number };
  signals: any[];
  live_posts: any[];
}

export function useAlgoPharmaAPI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAuthToken = () => localStorage.getItem('access_token');
  const getAuthRole = () => localStorage.getItem('user_role');

  const authHeaders = (): Record<string, string> => {
    const token = getAuthToken();
    const h: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  };

  const login = async (username: string, password: string): Promise<AuthResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      if (!res.ok) {
        throw new Error('Invalid credentials');
      }

      const data: AuthResponse = await res.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_name', data.name || username);
      localStorage.setItem('user_role', data.role || 'viewer');
      return data;
    } catch (err: any) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const register = async (username: string, password: string, role: string = 'admin'): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, email: username, role }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Registration failed');
      }
      return true;
    } catch (err: any) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_role');
    localStorage.removeItem('current_project_id');
    localStorage.removeItem('chat_state');
  };

  const sendChat = async (message: string): Promise<ChatResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const token = getAuthToken();
      if (!token) throw new Error('Not authenticated');

      const currentStateStr = localStorage.getItem('chat_state');
      const currentState = currentStateStr ? JSON.parse(currentStateStr) : { medicine: null, source: null, symptom: null, forum_url: null };

      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message, state: currentState }),
      });

      if (!res.ok) {
        throw new Error('Failed to start chat session');
      }

      const data: ChatResponse = await res.json();
      
      if (data.state) {
        localStorage.setItem('chat_state', JSON.stringify(data.state));
      }
      
      if (data.project_id) {
        localStorage.setItem('current_project_id', data.project_id.toString());
      }
      return data;
    } catch (err: any) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardData = useCallback(async (projectId: string): Promise<DashboardData | null> => {
    try {
      const token = getAuthToken();
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/results/${projectId}`, { headers });
      if (!res.ok) throw new Error('Failed to fetch dashboard data');

      const data = await res.json();
      const posts = data.posts || [];
      
      // Calculate aggregations
      const sources: Record<string, number> = {};
      const drugs: Record<string, number> = {};
      const symptoms: Record<string, number> = {};
      const sentiment = { positive: 0, neutral: 0, negative: 0 };
      
      posts.forEach((p: any) => {
        const platform = p.platform || 'unknown';
        sources[platform] = (sources[platform] || 0) + 1;
        
        const sent = (p.sentiment || 'NEUTRAL').toUpperCase();
        if (sent === 'POSITIVE') sentiment.positive++;
        else if (sent === 'NEGATIVE') sentiment.negative++;
        else sentiment.neutral++;
        
        p.drugs?.forEach((d: string) => {
          drugs[d] = (drugs[d] || 0) + 1;
        });
        
        p.symptoms?.forEach((s: string) => {
          symptoms[s] = (symptoms[s] || 0) + 1;
        });
      });

      return {
        status: data.status || 'unknown',
        total_raw: data.total_raw || data.counts?.total_raw || 0,
        processed: data.processed || data.counts?.processed_posts || 0,
        ae_flagged: data.ae_flagged || data.counts?.ae_flagged || 0,
        sources: sources,
        drug_counts: drugs,
        symptom_counts: symptoms,
        sentiment_distribution: sentiment,
        signals: (data.signals || []).map((s: any) => ({
          ...s,
          co_occurrences: s.post_count || s.co_occurrences || 0
        })),
        live_posts: posts
      };
    } catch (err: any) {
      setError(err.message);
      return null;
    }
  }, []);

  // ── Admin APIs ──
  // Backend returns flat arrays, not wrapped in { sources: [] } or { users: [] }

  const fetchAdminSources = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/sources`, { headers: authHeaders() });
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : (data.sources || []);
    } catch { return []; }
  };

  const testAdminSource = async (url: string, configJson: string) => {
    try {
      let parsedConfig: any;
      try { parsedConfig = JSON.parse(configJson); } catch { parsedConfig = {}; }

      const res = await fetch(`${API_BASE_URL}/admin/sources/test`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ server_url: url, config_json: parsedConfig }),
      });
      return res.ok ? res.json() : null;
    } catch { return null; }
  };

  const saveAdminSource = async (name: string, platform: string, url: string, configJson: string) => {
    try {
      let parsedConfig: any;
      try { parsedConfig = JSON.parse(configJson); } catch { parsedConfig = {}; }

      const res = await fetch(`${API_BASE_URL}/admin/sources`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ name, platform, url, config_json: parsedConfig }),
      });
      return res.ok;
    } catch { return false; }
  };

  const runAgenticOnboarding = async (url: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/onboarding/forum`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ forum_url: url }),
      });
      return res.ok ? res.json() : null;
    } catch { return null; }
  };

  const fetchAdminUsers = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/users`, { headers: authHeaders() });
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : (data.users || []);
    } catch { return []; }
  };

  const toggleUserRole = async (id: number, currentRole: string) => {
    try {
      const newRole = currentRole === 'admin' ? 'viewer' : 'admin';
      const res = await fetch(`${API_BASE_URL}/admin/users/${id}/role`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({ role: newRole }),
      });
      return res.ok;
    } catch { return false; }
  };

  const updateCredentials = async (key: string, value: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/admin/credentials`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify({ key_name: key, encrypted_value: value }),
      });
      return res.ok;
    } catch { return false; }
  };

  return {
    login,
    register,
    logout,
    sendChat,
    fetchDashboardData,
    fetchAdminSources,
    testAdminSource,
    saveAdminSource,
    runAgenticOnboarding,
    fetchAdminUsers,
    toggleUserRole,
    updateCredentials,
    loading,
    error,
    isAuthenticated: !!getAuthToken(),
    role: getAuthRole(),
  };
}
