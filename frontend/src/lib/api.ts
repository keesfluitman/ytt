// API client for YTT backend
// In dev, this proxies to localhost:8001
// In production, it uses the same origin

// API base URL configuration
const API_BASE = import.meta.env.DEV 
  ? 'http://localhost:8001/api'  // Development: separate backend
  : '/api';  // Production: same origin (FastAPI serves both)

export interface TranslationRequest {
  text?: string;
  source_lang: string;
  target_lang: string;
  provider?: string;
  entry_id?: string;
}

export interface TranslationResponse {
  original_text: string;
  translated_text: string;
  source_lang: string;
  target_lang: string;
  provider: string;
  processing_time?: number;
}

export interface YouTubeRequest {
  url: string;
  source_lang: string;
  target_lang?: string;
  use_cookies?: string;
  merge_lines?: boolean;
}

export interface YouTubeResponse {
  video_id: string;
  title: string;
  url: string;
  video_info: {
    title: string;
    duration: number;
    uploader: string;
    upload_date: string;
    description: string;
  };
  available_languages: string[];
  source_lang: string;
  source_transcript_raw?: string;
  source_transcript_processed?: string;
  target_lang?: string;
  target_transcript_raw?: string;
  target_transcript_processed?: string;
  entry_id?: string;  // ID for history entry
  cached?: boolean;  // Whether this came from cache
  translation_error?: string;  // Error message if translation failed
}

// Helper for API calls
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
    }
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `API error: ${response.status}`);
  }

  return response.json();
}

// Translation endpoints
export const translationAPI = {
  translate: async (data: TranslationRequest): Promise<TranslationResponse> => {
    const formData = new FormData();
    if (data.text) formData.append('text', data.text);
    formData.append('source_lang', data.source_lang);
    formData.append('target_lang', data.target_lang);
    if (data.provider) formData.append('provider', data.provider);
    if (data.entry_id) formData.append('entry_id', data.entry_id);

    return fetchAPI('/translate', {
      method: 'POST',
      body: formData
    });
  },

  translateFile: async (file: File, sourceLang: string, targetLang: string): Promise<TranslationResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_lang', sourceLang);
    formData.append('target_lang', targetLang);

    return fetchAPI('/translate', {
      method: 'POST',
      body: formData
    });
  },

  detectLanguage: async (text: string) => {
    const formData = new FormData();
    formData.append('text', text);

    return fetchAPI('/translate/detect', {
      method: 'POST',
      body: formData
    });
  },

  getLanguages: async () => {
    return fetchAPI('/languages');
  },

  getProviders: async () => {
    return fetchAPI('/providers');
  }
};

// YouTube endpoints
export const youtubeAPI = {
  fetchTranscript: async (data: YouTubeRequest): Promise<YouTubeResponse> => {
    return fetchAPI('/youtube/fetch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },

  getVideoInfo: async (url: string, useCookies = 'none') => {
    return fetchAPI('/youtube/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, use_cookies: useCookies })
    });
  },

  extractVideoId: async (url: string) => {
    return fetchAPI(`/youtube/extract-id?url=${encodeURIComponent(url)}`);
  }
};

// History endpoints
export const historyAPI = {
  getHistory: async (limit = 20, offset = 0) => {
    return fetchAPI(`/history?limit=${limit}&offset=${offset}`);
  },

  getTranslation: async (id: string) => {
    return fetchAPI(`/history/${id}`);
  },

  deleteTranslation: async (id: string) => {
    return fetchAPI(`/history/${id}`, { method: 'DELETE' });
  }
};

// Version info
export interface VersionInfo {
  version: string;
  build_date: string;
  git_commit: string;
}

export const getVersion = async (): Promise<VersionInfo> => {
  return fetchAPI('/version');
};

// Health check
export const healthCheck = async () => {
  const response = await fetch(`${API_BASE.replace('/api', '')}/health`);
  return response.json();
};