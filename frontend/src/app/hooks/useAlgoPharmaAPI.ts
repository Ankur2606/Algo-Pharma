import { useState, useCallback } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export interface AuthResponse {
  access_token: string;
  name: string;
  token_type: string;
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
      localStorage.setItem('user_name', data.name);
      return data;
    } catch (err: any) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_name');
    localStorage.removeItem('current_project_id');
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
        // Source
        const platform = p.platform || 'unknown';
        sources[platform] = (sources[platform] || 0) + 1;
        
        // Sentiment
        const sent = (p.sentiment || 'NEUTRAL').toUpperCase();
        if (sent === 'POSITIVE') sentiment.positive++;
        else if (sent === 'NEGATIVE') sentiment.negative++;
        else sentiment.neutral++;
        
        // Drugs
        p.drugs?.forEach((d: string) => {
          drugs[d] = (drugs[d] || 0) + 1;
        });
        
        // Symptoms
        p.symptoms?.forEach((s: string) => {
          symptoms[s] = (symptoms[s] || 0) + 1;
        });
      });

      // Ensure fallbacks to prevent undefined values in React components
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

  return {
    login,
    logout,
    sendChat,
    fetchDashboardData,
    loading,
    error,
    isAuthenticated: !!getAuthToken()
  };
}
