// Authentication Management
class AuthManager {
  constructor() {
    this.currentUser = null;
    this.isAuthenticated = false;
    this.init();
  }

  async init() {
    const token = localStorage.getItem('access_token');
    if (token) {
      api.setToken(token);
      // Verify token is valid by making a request
      try {
        await api.getOverview();
        this.isAuthenticated = true;
        this.showDashboard();
      } catch (error) {
        this.logout();
      }
    } else {
      this.showLogin();
    }
  }

  async login(email, password) {
    try {
      const data = await api.login(email, password);
      this.isAuthenticated = true;
      this.showDashboard();
      return data;
    } catch (error) {
      alert('Login failed: ' + error.message);
      throw error;
    }
  }

  async register(userData) {
    try {
      const data = await api.register(userData);
      this.isAuthenticated = true;
      this.showDashboard();
      return data;
    } catch (error) {
      alert('Registration failed: ' + error.message);
      throw error;
    }
  }

  logout() {
    api.clearToken();
    this.isAuthenticated = false;
    this.currentUser = null;
    this.showLogin();
  }

  showLogin() {
    // Hide all pages
    document.querySelectorAll('.page-wrapper').forEach(page => {
      page.style.display = 'none';
    });
    
    // Show login page
    const loginPage = document.getElementById('login-page');
    if (loginPage) {
      loginPage.style.display = 'block';
    } else {
      // Create login page if it doesn't exist
      this.createLoginPage();
    }
  }

  showDashboard() {
    // Hide all pages
    document.querySelectorAll('.page-wrapper').forEach(page => {
      page.style.display = 'none';
    });
    
    // Show dashboard page
    const dashboardPage = document.getElementById('dashboard-page');
    if (dashboardPage) {
      dashboardPage.style.display = 'block';
      // Load dashboard data
      if (window.dashboardManager) {
        window.dashboardManager.loadDashboard();
      }
    } else {
      // Create dashboard page if it doesn't exist
      this.createDashboardPage();
    }
  }

  createLoginPage() {
    const loginHTML = `
      <div id="login-page" class="page-wrapper" style="display: block;">
        <div class="auth-container">
          <div class="auth-card">
            <div class="auth-header">
              <h1 class="auth-title">Cashflow AI</h1>
              <p class="auth-subtitle">Manage your business finances with AI</p>
            </div>
            
            <form id="login-form" class="auth-form">
              <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required>
              </div>
              
              <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
              </div>
              
              <button type="submit" class="btn btn-primary btn-full">Login</button>
            </form>
            
            <div class="auth-divider">
              <span>or</span>
            </div>
            
            <div class="oauth-buttons">
              <button id="google-login" class="btn btn-outline btn-full">
                <span class="btn-icon">G</span>
                Continue with Google
              </button>
              
              <button id="microsoft-login" class="btn btn-outline btn-full">
                <span class="btn-icon">M</span>
                Continue with Microsoft
              </button>
            </div>
            
            <div class="auth-footer">
              <p>Don't have an account? <a href="#" id="show-register">Sign up</a></p>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.getElementById('app').insertAdjacentHTML('beforeend', loginHTML);
    this.attachLoginListeners();
  }

  createDashboardPage() {
    // Use the existing dashboard HTML from UX1
    const dashboardHTML = `
      <div id="dashboard-page" class="page-wrapper">
        <!-- Navigation -->
        <nav class="navbar">
          <div class="nav-container">
            <div class="nav-brand">
              <span class="brand-icon">💰</span>
              <span class="brand-text">Cashflow AI</span>
            </div>
            
            <div class="nav-menu">
              <a href="#" class="nav-link active" data-page="dashboard">Dashboard</a>
              <a href="#" class="nav-link" data-page="transactions">Transactions</a>
              <a href="#" class="nav-link" data-page="import">Import</a>
            </div>
            
            <div class="nav-actions">
              <button id="logout-btn" class="btn btn-outline">Logout</button>
            </div>
          </div>
        </nav>
        
        <!-- Main Content -->
        <main class="main-content">
          <div class="content-header">
            <h1>Dashboard</h1>
            <p>Overview of your financial data</p>
          </div>
          
          <!-- KPI Cards -->
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-icon">💰</div>
              <div class="kpi-content">
                <h3>Cash Balance</h3>
                <div class="kpi-value" id="cash-balance">$0</div>
              </div>
            </div>
            
            <div class="kpi-card">
              <div class="kpi-icon">📈</div>
              <div class="kpi-content">
                <h3>Revenue (This Month)</h3>
                <div class="kpi-value" id="revenue">$0</div>
              </div>
            </div>
            
            <div class="kpi-card">
              <div class="kpi-icon">📉</div>
              <div class="kpi-content">
                <h3>Expenses (This Month)</h3>
                <div class="kpi-value" id="expenses">$0</div>
              </div>
            </div>
            
            <div class="kpi-card">
              <div class="kpi-icon">📊</div>
              <div class="kpi-content">
                <h3>Net Income</h3>
                <div class="kpi-value" id="net-income">$0</div>
              </div>
            </div>
          </div>
          
          <!-- Charts Section -->
          <div class="charts-section">
            <div class="chart-container">
              <h2>Revenue vs Expenses</h2>
              <div id="revenue-chart"></div>
            </div>
          </div>
          
          <!-- Top Customers & Suppliers -->
          <div class="top-section">
            <div class="top-card">
              <h2>Top Customers</h2>
              <div id="top-customers"></div>
            </div>
            
            <div class="top-card">
              <h2>Top Suppliers</h2>
              <div id="top-suppliers"></div>
            </div>
          </div>
        </main>
      </div>
    `;
    
    document.getElementById('app').insertAdjacentHTML('beforeend', dashboardHTML);
    this.attachDashboardListeners();
  }

  attachLoginListeners() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        try {
          await this.login(email, password);
        } catch (error) {
          console.error('Login error:', error);
        }
      });
    }

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => this.logout());
    }
  }

  attachDashboardListeners() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => this.logout());
    }
  }
}

// Global auth instance
const authManager = new AuthManager();
