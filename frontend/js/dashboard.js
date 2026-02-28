// ========================================
// DASHBOARD INTERACTIVE FEATURES
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    initChart();
    initAlerts();
    animateKPIs();
});

// ========================================
// CHART RENDERING (Canvas-based)
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
