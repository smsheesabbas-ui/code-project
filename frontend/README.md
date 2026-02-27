# 🔥 Cashflow — UX Package

## What's included

| File | Description |
|------|-------------|
| `cashflow_interactive.html` | ✅ **START HERE** — Single-file interactive SPA demo (no server needed) |
| `index.html` | Homepage (multi-page version) |
| `dashboard.html` | Dashboard page |
| `transactions.html` | Transactions page |
| `css/style.css` | Shared design system & sidebar styles |
| `css/dashboard.css` | Dashboard-specific styles |
| `css/transactions.css` | Transactions-specific styles |
| `js/app.js` | Sidebar, navigation & animations |
| `js/dashboard.js` | Chart, KPI animations, alerts |

## How to use

### Option A — Interactive SPA (recommended)
Just open `cashflow_interactive.html` in any browser.
- All pages in one file, no server required.
- Click the top nav bar or sidebar links to switch pages.

### Option B — Multi-page site
Open `index.html` in a browser **via a local server** so href links work correctly.
```bash
# Python 3
python -m http.server 8080
# Then visit: http://localhost:8080
```

## Features
- ☰ Hamburger opens sidebar → icon disappears; click backdrop to close → icon reappears
- 🏠 Back to Home button on every inner page
- 📊 Animated KPI counters & Revenue vs Expenses chart
- 🔍 Live transaction search filter
- 🎨 Warm color palette (orange, green, cream)
- 📱 Responsive design
