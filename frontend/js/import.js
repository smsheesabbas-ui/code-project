// CSV Import Management
class ImportManager {
  constructor() {
    this.currentImport = null;
    this.file = null;
  }

  async handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      alert('Please select a CSV file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('File too large. Maximum size is 10MB');
      return;
    }

    this.file = file;
    await this.uploadFile();
  }

  async uploadFile() {
    try {
      // Show loading state
      this.showLoading('Uploading file...');

      // Upload file
      const importData = await api.uploadCSV(this.file);
      this.currentImport = importData;

      // Process and show preview
      await this.showPreview();

    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed: ' + error.message);
      this.hideLoading();
    }
  }

  async showPreview() {
    try {
      this.showLoading('Processing CSV...');

      const preview = await api.getImportPreview(this.currentImport.id);
      this.renderPreview(preview);

    } catch (error) {
      console.error('Preview failed:', error);
      alert('Failed to generate preview: ' + error.message);
    } finally {
      this.hideLoading();
    }
  }

  renderPreview(preview) {
    const container = document.getElementById('import-preview');
    if (!container) return;

    const confidence = (preview.detection_confidence * 100).toFixed(1);
    const hasErrors = preview.validation_summary.error_rows > 0;

    container.innerHTML = `
      <div class="import-header">
        <h2>Import Preview</h2>
        <div class="import-stats">
          <div class="stat">
            <span class="stat-label">Total Rows:</span>
            <span class="stat-value">${preview.total_rows}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Valid:</span>
            <span class="stat-value">${preview.validation_summary.valid_rows}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Errors:</span>
            <span class="stat-value ${hasErrors ? 'error' : ''}">${preview.validation_summary.error_rows}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Confidence:</span>
            <span class="stat-value">${confidence}%</span>
          </div>
        </div>
      </div>

      <div class="column-mapping">
        <h3>Detected Columns</h3>
        <div class="mapping-grid">
          <div class="mapping-item">
            <label>Date:</label>
            <select id="date-column" data-field="date">
              <option value="">Not detected</option>
              ${this.getColumnOptions(preview.column_mapping.date)}
            </select>
          </div>
          <div class="mapping-item">
            <label>Description:</label>
            <select id="description-column" data-field="description">
              <option value="">Not detected</option>
              ${this.getColumnOptions(preview.column_mapping.description)}
            </select>
          </div>
          <div class="mapping-item">
            <label>Amount:</label>
            <select id="amount-column" data-field="amount">
              <option value="">Not detected</option>
              ${this.getColumnOptions(preview.column_mapping.amount)}
            </select>
          </div>
          <div class="mapping-item">
            <label>Debit:</label>
            <select id="debit-column" data-field="debit">
              <option value="">Not detected</option>
              ${this.getColumnOptions(preview.column_mapping.debit)}
            </select>
          </div>
          <div class="mapping-item">
            <label>Credit:</label>
            <select id="credit-column" data-field="credit">
              <option value="">Not detected</option>
              ${this.getColumnOptions(preview.column_mapping.credit)}
            </select>
          </div>
        </div>
      </div>

      <div class="preview-table">
        <h3>Preview Data</h3>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Row</th>
                <th>Date</th>
                <th>Description</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${preview.rows.slice(0, 20).map(row => `
                <tr class="${row.validation_errors.length > 0 ? 'error-row' : ''}">
                  <td>${row.row_number}</td>
                  <td>${row.date || 'Invalid'}</td>
                  <td>${row.description || ''}</td>
                  <td>${row.amount !== null ? '$' + row.amount.toFixed(2) : 'Invalid'}</td>
                  <td>
                    ${row.validation_errors.length > 0 
                      ? `<span class="error-badge">${row.validation_errors.join(', ')}</span>`
                      : '<span class="success-badge">Valid</span>'
                    }
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <div class="import-actions">
        <button id="update-mapping" class="btn btn-secondary">Update Mapping</button>
        <button id="confirm-import" class="btn btn-primary">Import Transactions</button>
        <button id="cancel-import" class="btn btn-outline">Cancel</button>
      </div>
    `;

    this.attachPreviewListeners();
  }

  getColumnOptions(selectedValue) {
    // This would need to be dynamic based on actual CSV columns
    const columns = ['Date', 'Description', 'Amount', 'Debit', 'Credit', 'Balance'];
    return columns.map(col => 
      `<option value="${col}" ${col === selectedValue ? 'selected' : ''}>${col}</option>`
    ).join('');
  }

  attachPreviewListeners() {
    const updateBtn = document.getElementById('update-mapping');
    const confirmBtn = document.getElementById('confirm-import');
    const cancelBtn = document.getElementById('cancel-import');

    if (updateBtn) {
      updateBtn.addEventListener('click', () => this.updateMapping());
    }

    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => this.confirmImport());
    }

    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.cancelImport());
    }
  }

  async updateMapping() {
    try {
      const mapping = {
        date: document.getElementById('date-column').value || null,
        description: document.getElementById('description-column').value || null,
        amount: document.getElementById('amount-column').value || null,
        debit: document.getElementById('debit-column').value || null,
        credit: document.getElementById('credit-column').value || null,
        balance: null
      };

      await api.updateColumnMapping(this.currentImport.id, mapping);
      await this.showPreview(); // Refresh preview

    } catch (error) {
      console.error('Failed to update mapping:', error);
      alert('Failed to update mapping: ' + error.message);
    }
  }

  async confirmImport() {
    try {
      this.showLoading('Importing transactions...');

      const result = await api.confirmImport(this.currentImport.id);
      
      alert(`Successfully imported ${result.imported_count} transactions!`);
      this.hideImportPage();
      
      // Redirect to transactions page
      if (window.pageManager) {
        window.pageManager.showPage('transactions');
      }

    } catch (error) {
      console.error('Import failed:', error);
      alert('Import failed: ' + error.message);
    } finally {
      this.hideLoading();
    }
  }

  cancelImport() {
    this.hideImportPage();
  }

  hideImportPage() {
    const container = document.getElementById('import-preview');
    if (container) {
      container.innerHTML = '';
    }
    this.currentImport = null;
    this.file = null;
  }

  showLoading(message) {
    const loadingHTML = `
      <div class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">${message}</div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingHTML);
  }

  hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
      overlay.remove();
    }
  }
}

// Global import manager
window.importManager = new ImportManager();
