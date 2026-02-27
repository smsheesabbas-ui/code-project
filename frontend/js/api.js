// API Configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api.cashflow.ai/api/v1' 
  : 'http://localhost:8000/api/v1';

// Fallback for development without /api/v1 prefix
const FALLBACK_API_URL = 'http://localhost:8000';

// API Client
class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('access_token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
      }

      return await response.json();
    } catch (error) {
      // Try fallback URL if main fails
      if (this.baseURL === API_BASE_URL && !endpoint.startsWith('/auth')) {
        console.log('Trying fallback API URL...');
        const fallbackUrl = `${FALLBACK_API_URL}${endpoint}`;
        const fallbackResponse = await fetch(fallbackUrl, config);
        
        if (fallbackResponse.ok) {
          return await fallbackResponse.json();
        }
      }
      
      console.error('API Error:', error);
      throw error;
    }
  }

  // Auth endpoints
  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async register(userData) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    this.setToken(data.access_token);
    return data;
  }

  async logout() {
    await this.request('/auth/logout', { method: 'POST' });
    this.clearToken();
  }

  // Dashboard endpoints
  async getOverview() {
    return this.request('/dashboard/overview');
  }

  async getTopCustomers(limit = 10) {
    return this.request(`/dashboard/top-customers?limit=${limit}`);
  }

  async getTopSuppliers(limit = 10) {
    return this.request(`/dashboard/top-suppliers?limit=${limit}`);
  }

  async getTransactions(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/dashboard/transactions?${query}`);
  }

  // CSV Import endpoints
  async uploadCSV(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/imports/upload`, {
      method: 'POST',
      headers: this.token ? { Authorization: `Bearer ${this.token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }

  async getImportPreview(importId) {
    return this.request(`/imports/${importId}/preview`);
  }

  async updateColumnMapping(importId, mapping) {
    return this.request(`/imports/${importId}/column-mapping`, {
      method: 'PUT',
      body: JSON.stringify(mapping),
    });
  }

  async confirmImport(importId, duplicateAction = 'skip') {
    return this.request(`/imports/${importId}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ duplicate_action: duplicateAction }),
    });
  }

  async getImports() {
    return this.request('/imports/');
  }
}

// Global API instance
const api = new ApiClient();
