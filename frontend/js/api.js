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
        const token = localStorage.getItem('cashflow_token');
        if (!token) throw new Error('No token found');
        
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
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
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/imports/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        return response.json();
    }
    
    static async getImportPreview(importId) {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/imports/${importId}/preview`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get preview');
        }
        
        return response.json();
    }
    
    static async updateColumnMapping(importId, mapping) {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/imports/${importId}/column-mapping`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
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
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/imports/${importId}/confirm`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to confirm import');
        }
        
        return response.json();
    }
    
    static async listImports() {
        const token = AuthAPI.getToken();
        if (!token) throw new Error('Not authenticated');
        
        const response = await fetch(`${API_BASE_URL}/imports`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
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
    handleAPIError,
    formatCurrency,
    formatDate
};
