// ========================================
// DASHBOARD INTERACTIVE FEATURES
// ========================================

class DashboardManager {
  constructor() {
    this.data = null;
    this.chart = null;
  }

  async loadDashboard() {
    try {
      // Load overview data
      const overview = await api.getOverview();
      this.updateKPIs(overview);
      
      // Load top customers and suppliers
      const [customers, suppliers] = await Promise.all([
        api.getTopCustomers(10),
        api.getTopSuppliers(10)
      ]);
      
      this.updateTopCustomers(customers);
      this.updateTopSuppliers(suppliers);
      
      // Load transactions for chart
      const transactions = await api.getTransactions({ limit: 100 });
      this.updateChart(transactions.transactions);
      
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      this.showError('Failed to load dashboard data');
    }
  }

  updateKPIs(overview) {
    // Update KPI values with animation
    this.animateValue('cash-balance', overview.cash_balance || 0);
    this.animateValue('revenue', overview.total_revenue_this_month || 0);
    this.animateValue('expenses', overview.total_expenses_this_month || 0);
    this.animateValue('net-income', overview.net_income_this_month || 0);
  }

  updateTopCustomers(customers) {
    const container = document.getElementById('top-customers');
    if (!container) return;
    
    container.innerHTML = customers.map(customer => `
      <div class="top-item">
        <div class="top-name">${customer.name}</div>
        <div class="top-amount">$${customer.total_amount.toFixed(2)}</div>
      </div>
    `).join('');
  }

  updateTopSuppliers(suppliers) {
    const container = document.getElementById('top-suppliers');
    if (!container) return;
    
    container.innerHTML = suppliers.map(supplier => `
      <div class="top-item">
        <div class="top-name">${supplier.name}</div>
        <div class="top-amount">$${supplier.total_amount.toFixed(2)}</div>
      </div>
    `).join('');
  }

  updateChart(transactions) {
    // Group transactions by month
    const monthlyData = this.groupTransactionsByMonth(transactions);
    
    const canvas = document.getElementById('revenue-chart');
    if (!canvas) return;
    
    // Create canvas element if it doesn't exist
    if (canvas.tagName !== 'CANVAS') {
      const canvasEl = document.createElement('canvas');
      canvasEl.id = 'revenue-chart';
      canvasEl.width = canvas.offsetWidth || 600;
      canvasEl.height = 300;
      canvas.innerHTML = '';
      canvas.appendChild(canvasEl);
      this.drawChart(canvasEl, monthlyData);
    } else {
      this.drawChart(canvas, monthlyData);
    }
  }

  groupTransactionsByMonth(transactions) {
    const monthly = {};
    
    transactions.forEach(tx => {
      const date = new Date(tx.transaction_date);
      const monthKey = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      
      if (!monthly[monthKey]) {
        monthly[monthKey] = { revenue: 0, expenses: 0 };
      }
      
      if (tx.amount > 0) {
        monthly[monthKey].revenue += tx.amount;
      } else {
        monthly[monthKey].expenses += Math.abs(tx.amount);
      }
    });
    
    return monthly;
  }

  drawChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    const months = Object.keys(data);
    const values = months.map(month => ({
      revenue: data[month].revenue,
      expenses: data[month].expenses
    }));
    
    const maxValue = Math.max(
      ...values.flatMap(v => [v.revenue, v.expenses])
    );
    
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const barWidth = chartWidth / (months.length * 2 + months.length - 1);
    
    // Draw bars
    months.forEach((month, index) => {
      const x = padding + index * (barWidth * 2 + barWidth);
      
      // Revenue bar
      const revenueHeight = (data[month].revenue / maxValue) * chartHeight;
      ctx.fillStyle = '#16a34a';
      ctx.fillRect(x, height - padding - revenueHeight, barWidth, revenueHeight);
      
      // Expenses bar
      const expensesHeight = (data[month].expenses / maxValue) * chartHeight;
      ctx.fillStyle = '#ef4444';
      ctx.fillRect(x + barWidth, height - padding - expensesHeight, barWidth, expensesHeight);
      
      // Month label
      ctx.fillStyle = '#666';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(month, x + barWidth, height - padding + 20);
    });
    
    // Draw axes
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();
  }

  animateValue(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const startValue = 0;
    const duration = 1000;
    const startTime = performance.now();
    
    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const currentValue = startValue + (targetValue - startValue) * progress;
      element.textContent = `$${currentValue.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }

  showError(message) {
    // Show error message in dashboard
    const errorHTML = `<div class="error-message">${message}</div>`;
    const container = document.querySelector('.main-content');
    if (container) {
      container.insertAdjacentHTML('afterbegin', errorHTML);
      setTimeout(() => {
        const errorEl = container.querySelector('.error-message');
        if (errorEl) errorEl.remove();
      }, 5000);
    }
  }
}

// Global dashboard manager
window.dashboardManager = new DashboardManager();

// Legacy compatibility
document.addEventListener('DOMContentLoaded', function() {
    initChart();
    initAlerts();
    animateKPIs();
});

// ========================================
// CHART RENDERING (Canvas-based) - Legacy
// ========================================

function initChart() {
    const canvas = document.getElementById('revenueChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    
    // Set canvas size
    canvas.width = container.offsetWidth;
    canvas.height = container.offsetHeight;
    
    // Sample data (last 6 months)
    const data = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        revenue: [15200, 16800, 14500, 17200, 16400, 18240],
        expenses: [10800, 11200, 10500, 11800, 10800, 12450]
    };
    
    drawBarChart(ctx, canvas, data);
    
    // Redraw on window resize
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            canvas.width = container.offsetWidth;
            canvas.height = container.offsetHeight;
            drawBarChart(ctx, canvas, data);
        }, 250);
    });
}

function drawBarChart(ctx, canvas, data) {
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Find max value for scaling
    const maxValue = Math.max(...data.revenue, ...data.expenses);
    const scale = chartHeight / (maxValue * 1.1); // Add 10% headroom
    
    // Calculate bar dimensions
    const barCount = data.labels.length;
    const groupWidth = chartWidth / barCount;
    const barWidth = (groupWidth - 20) / 2; // 2 bars per group with spacing
    
    // Colors — warm palette
    const revenueColor = '#16a34a';
    const expenseColor = '#f97316';
    const gridColor = '#e7e5e4';
    const textColor = '#78716c';
    
    // Draw grid lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }
    
    // Draw bars
    data.labels.forEach((label, i) => {
        const x = padding + (groupWidth * i) + 10;
        
        // Revenue bar
        const revenueHeight = data.revenue[i] * scale;
        const revenueY = padding + chartHeight - revenueHeight;
        ctx.fillStyle = revenueColor;
        drawRoundedRect(ctx, x, revenueY, barWidth, revenueHeight, 4);
        
        // Expense bar
        const expenseHeight = data.expenses[i] * scale;
        const expenseY = padding + chartHeight - expenseHeight;
        ctx.fillStyle = expenseColor;
        drawRoundedRect(ctx, x + barWidth + 4, expenseY, barWidth, expenseHeight, 4);
        
        // Label
        ctx.fillStyle = textColor;
        ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(label, x + barWidth + 2, height - padding + 20);
    });
    
    // Draw Y-axis labels
    ctx.fillStyle = textColor;
    ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
        const value = Math.round((maxValue * 1.1 / 4) * (4 - i));
        const y = padding + (chartHeight / 4) * i;
        ctx.fillText('$' + (value / 1000).toFixed(0) + 'k', padding - 10, y + 4);
    }
    
    // Draw legend
    const legendY = 20;
    ctx.fillStyle = revenueColor;
    drawRoundedRect(ctx, width - 140, legendY, 12, 12, 2);
    ctx.fillStyle = textColor;
    ctx.font = '13px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Revenue', width - 122, legendY + 10);
    
    ctx.fillStyle = expenseColor;
    drawRoundedRect(ctx, width - 140, legendY + 20, 12, 12, 2);
    ctx.fillStyle = textColor;
    ctx.fillText('Expenses', width - 122, legendY + 30);
}

function drawRoundedRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    ctx.fill();
}

// ========================================
// ALERT INTERACTIONS
// ========================================

function initAlerts() {
    const alertCloseButtons = document.querySelectorAll('.alert-close');
    
    alertCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.closest('.alert-banner');
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                alert.style.display = 'none';
            }, 200);
        });
    });
}

// ========================================
// KPI ANIMATIONS
// ========================================

function animateKPIs() {
    const kpiValues = document.querySelectorAll('.kpi-value');
    
    kpiValues.forEach(element => {
        const finalValue = element.textContent;
        
        // Only animate numbers (skip if it contains non-numeric characters except $,)
        if (!/^[\$,\d.]+$/.test(finalValue)) return;
        
        const numericValue = parseFloat(finalValue.replace(/[$,]/g, ''));
        const duration = 1000;
        const startTime = performance.now();
        
        function animate(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = numericValue * easeOut;
            
            // Format the number
            if (finalValue.includes('$')) {
                element.textContent = '$' + Math.round(currentValue).toLocaleString();
            } else {
                element.textContent = Math.round(currentValue).toLocaleString();
            }
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = finalValue; // Ensure final value is exact
            }
        }
        
        requestAnimationFrame(animate);
    });
}

// ========================================
// PERIOD SELECTOR
// ========================================

document.querySelectorAll('.period-selector').forEach(selector => {
    selector.addEventListener('change', function() {
        // In a real app, this would fetch new data and redraw the chart
        console.log('Period changed to:', this.value);
        
        // Show loading state
        const card = this.closest('.card');
        card.style.opacity = '0.6';
        
        // Simulate data fetch
        setTimeout(() => {
            card.style.opacity = '1';
        }, 500);
    });
});
