// ========================================
// CASHFLOW - API INTEGRATION
// Connects frontend to FastAPI backend
// ========================================

const API_BASE_URL = 'http://localhost:8000/api/v1';

// ========================================
// AUTHENTICATION API
// ========================================

class AuthAPI {
    static async register(userData) {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        
        return response.json();
    }
    
    static async login(credentials) {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        const data = await response.json();
        // Store token in localStorage
        localStorage.setItem('cashflow_token', data.access_token);
        localStorage.setItem('cashflow_user', JSON.stringify(data.user));
        
        return data;
    }
    
    static async getCurrentUser() {
        const response = await fetch(`${API_BASE_URL}/auth/me`);
        
        if (!response.ok) {
            throw new Error('Failed to get user');
        }
        
        return response.json();
    }
    
    static logout() {
        localStorage.removeItem('cashflow_token');
        localStorage.removeItem('cashflow_user');
    }
    
    static getToken() {
        return localStorage.getItem('cashflow_token');
    }
    
    static isAuthenticated() {
        return !!this.getToken();
    }
    
    static getCurrentUserFromStorage() {
        const userStr = localStorage.getItem('cashflow_user');
        return userStr ? JSON.parse(userStr) : null;
    }
}

// ========================================
// CSV IMPORT API
// ========================================

class ImportAPI {
    static async uploadCSV(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_BASE_URL}/imports/upload`, {
                method: 'POST',
                body: formData
            });
            
            console.log('Upload response status:', response.status);
            console.log('Upload response headers:', response.headers);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Upload error response:', errorText);
                throw new Error(errorText || 'Upload failed');
            }
            
            const data = await response.json();
            console.log('Upload success data:', data);
            return data;
        } catch (error) {
            console.error('Upload fetch error:', error);
            throw new Error(`Upload failed: ${error.message}`);
        }
    }
    
    static async getImportPreview(importId) {
        const response = await fetch(`${API_BASE_URL}/imports/${importId}/preview`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get preview');
        }
        
        return response.json();
    }
    
    static async updateColumnMapping(importId, mapping) {
        const response = await fetch(`${API_BASE_URL}/imports/${importId}/column-mapping`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mapping)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update mapping');
        }
        
        return response.json();
    }
    
    static async confirmImport(importId) {
        const response = await fetch(`${API_BASE_URL}/imports/${importId}/confirm`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to confirm import');
        }
        
        return response.json();
    }
    
    static async listImports() {
        const response = await fetch(`${API_BASE_URL}/imports`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to list imports');
        }
        
        return response.json();
    }
}

// ========================================
// TRANSACTIONS API
// ========================================

class TransactionAPI {
    static async createTransaction(transactionData) {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/transactions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(transactionData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create transaction');
        }
        
        return response.json();
    }
    
    static async getTransactions(page = 1, perPage = 20, filters = {}) {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const params = new URLSearchParams({
            page: page.toString(),
            per_page: perPage.toString(),
            ...filters
        });
        
        const response = await fetch(`${API_BASE_URL}/transactions?${params}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get transactions');
        }
        
        return response.json();
    }
    
    static async getTransaction(transactionId) {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get transaction');
        }
        
        return response.json();
    }
    
    static async updateTransaction(transactionId, updateData) {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update transaction');
        }
        
        return response.json();
    }
    
    static async deleteTransaction(transactionId) {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete transaction');
        }
        
        return response.json();
    }
}

// ========================================
// DASHBOARD API
// ========================================

class DashboardAPI {
    static async getOverview() {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/dashboard/overview`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get dashboard data');
        }
        
        return response.json();
    }
    
    static async getTopCustomers() {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/dashboard/top-customers`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get top customers');
        }
        
        return response.json();
    }
    
    static async getTopSuppliers() {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/dashboard/top-suppliers`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get top suppliers');
        }
        
        return response.json();
    }
    
    static async getMonthlyTrend(months = 6) {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/dashboard/monthly-trend?months=${months}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get monthly trend');
        }
        
        return response.json();
    }
}

// ========================================
// INTELLIGENCE API
// ========================================

class IntelligenceAPI {
    static async getWeeklySummary() {
        const response = await fetch(`${API_BASE_URL}/intelligence/weekly-summary`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get weekly summary');
        }
        
        return response.json();
    }
    
    static async getRecommendations() {
        const response = await fetch(`${API_BASE_URL}/intelligence/recommendations`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get recommendations');
        }
        
        return response.json();
    }
    
    static async getCashflowForecast(days = 30) {
        const response = await fetch(`${API_BASE_URL}/intelligence/forecasts/cashflow?days=${days}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get forecast');
        }
        
        return response.json();
    }
    
    static async getAlerts(limit = 50) {
        const response = await fetch(`${API_BASE_URL}/intelligence/alerts?limit=${limit}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get alerts');
        }
        
        return response.json();
    }
    
    static async checkAlerts() {
        const response = await fetch(`${API_BASE_URL}/intelligence/alerts/check`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to check alerts');
        }
        
        return response.json();
    }
    
    static async acknowledgeAlert(alertId) {
        const response = await fetch(`${API_BASE_URL}/intelligence/alerts/${alertId}/acknowledge`, {
            method: 'PUT'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to acknowledge alert');
        }
        
        return response.json();
    }
    
    static async extractEntity(description) {
        const response = await fetch(`${API_BASE_URL}/intelligence/extract-entity`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to extract entity');
        }
        
        return response.json();
    }
    
    static async classifyCategory(description, amount) {
        const response = await fetch(`${API_BASE_URL}/intelligence/classify-category`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description, amount })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to classify category');
        }
        
        return response.json();
    }
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function handleAPIError(error) {
    console.error('API Error:', error);
    
    // Show user-friendly error message
    const errorMessage = error.message || 'An unexpected error occurred';
    
    // You can implement a toast notification or alert here
    alert(errorMessage);
    
    // If it's an authentication error, redirect to login
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        AuthAPI.logout();
        window.location.href = '#login';
    }
}

function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ========================================
// EXPORT
// ========================================

window.CashflowAPI = {
    Auth: AuthAPI,
    Import: ImportAPI,
    Transaction: TransactionAPI,
    Dashboard: DashboardAPI,
    Intelligence: IntelligenceAPI,
    handleAPIError,
    formatCurrency,
    formatDate
};
