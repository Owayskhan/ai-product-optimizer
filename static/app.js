class AIOptimizer {
    constructor() {
        this.apiUrl = window.location.origin + '/api';
        this.currentTab = 'dashboard';
        this.batchResults = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkApiStatus();
        this.updateDashboard();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Product form
        document.getElementById('product-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.optimizeSingleProduct();
        });

        // CSV upload
        document.getElementById('csv-file').addEventListener('change', (e) => {
            this.handleCsvUpload(e.target.files[0]);
        });

        document.getElementById('upload-box').addEventListener('click', () => {
            document.getElementById('csv-file').click();
        });

        // Download template
        document.getElementById('download-template').addEventListener('click', () => {
            this.downloadTemplate();
        });

        // Close error
        document.getElementById('close-error').addEventListener('click', () => {
            this.hideError();
        });
    }

    switchTab(tab) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tab).classList.add('active');

        this.currentTab = tab;
    }

    async checkApiStatus() {
        try {
            const response = await fetch(`${this.apiUrl}/test-key`);
            const data = await response.json();
            
            const statusElement = document.getElementById('api-status');
            if (data.status === 'success') {
                statusElement.textContent = 'API Ready';
                statusElement.style.background = 'rgba(34, 197, 94, 0.2)';
            } else {
                statusElement.textContent = 'API Error';
                statusElement.style.background = 'rgba(239, 68, 68, 0.2)';
                this.showError('API key not working: ' + data.message);
            }
        } catch (error) {
            document.getElementById('api-status').textContent = 'API Error';
            this.showError('Failed to connect to API');
        }
    }

    async optimizeSingleProduct() {
        const formData = new FormData(document.getElementById('product-form'));
        const productData = {};
        
        for (let [key, value] of formData.entries()) {
            if (key === 'price' || key === 'weight') {
                productData[key] = value ? parseFloat(value) : null;
            } else {
                productData[key] = value || null;
            }
        }

        // Remove null values
        Object.keys(productData).forEach(key => {
            if (productData[key] === null || productData[key] === '') {
                delete productData[key];
            }
        });

        this.showLoading();
        try {
            const response = await fetch(`${this.apiUrl}/optimize-product`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.displayOptimizationResults(result);
        } catch (error) {
            this.showError('Optimization failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async handleCsvUpload(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        this.showLoading();
        try {
            const response = await fetch(`${this.apiUrl}/upload-csv`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            await this.optimizeBatch(result.products);
        } catch (error) {
            this.showError('CSV upload failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async optimizeBatch(products) {
        try {
            const response = await fetch(`${this.apiUrl}/optimize-batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ products })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.batchResults.unshift(result);
            this.updateDashboard();
            this.displayBatchResults(result);
            this.switchTab('dashboard');
        } catch (error) {
            this.showError('Batch optimization failed: ' + error.message);
        }
    }

    displayOptimizationResults(result) {
        const resultsDiv = document.getElementById('optimization-results');
        const contentDiv = document.getElementById('results-content');
        
        contentDiv.innerHTML = `
            <div class="result-section">
                <h4>Optimization Score: ${Math.round(result.optimization_score * 100)}%</h4>
                <div style="width: 100%; background: #e0e0e0; border-radius: 10px; height: 20px;">
                    <div style="width: ${result.optimization_score * 100}%; background: #667eea; height: 100%; border-radius: 10px;"></div>
                </div>
            </div>
            
            <div class="result-section">
                <h4>AI Optimized Title</h4>
                <p>${result.ai_title}</p>
            </div>
            
            <div class="result-section">
                <h4>AI Optimized Description</h4>
                <p>${result.ai_description}</p>
            </div>
            
            <div class="result-section">
                <h4>Semantic Tags</h4>
                <div class="tags">
                    ${result.semantic_tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
            
            <div class="result-section">
                <h4>Use Cases</h4>
                <ul>
                    ${result.use_cases.map(useCase => `<li>${useCase}</li>`).join('')}
                </ul>
            </div>
            
            <div class="result-section">
                <h4>FAQ Content</h4>
                ${result.faq_content.map(faq => `
                    <div class="faq-item">
                        <div class="faq-question">${faq.question}</div>
                        <div class="faq-answer">${faq.answer}</div>
                    </div>
                `).join('')}
            </div>
            
            <div class="result-section">
                <h4>AI Summary</h4>
                <p>${result.ai_summary}</p>
            </div>
        `;
        
        resultsDiv.classList.remove('hidden');
    }

    displayBatchResults(result) {
        const resultsDiv = document.getElementById('batch-results');
        const contentDiv = document.getElementById('batch-content');
        
        contentDiv.innerHTML = `
            <div class="result-section">
                <h4>Batch Summary</h4>
                <p>Total Products: ${result.summary.total_products}</p>
                <p>Successfully Optimized: ${result.summary.successful}</p>
                <p>Failed: ${result.summary.failed}</p>
                <p>Average Score: ${Math.round(result.summary.average_score * 100)}%</p>
                <p>Processing Time: ${result.summary.processing_time.toFixed(2)}s</p>
            </div>
            
            <div class="result-section">
                <h4>Export Options</h4>
                <button class="btn btn-secondary" onclick="aiOptimizer.exportFeed('${result.batch_id}', 'google')">
                    <i class="fas fa-download"></i> Google Merchant XML
                </button>
                <button class="btn btn-secondary" onclick="aiOptimizer.exportFeed('${result.batch_id}', 'meta')">
                    <i class="fas fa-download"></i> Meta/TikTok CSV
                </button>
            </div>
        `;
        
        resultsDiv.classList.remove('hidden');
    }

    async exportFeed(batchId, type) {
        const endpoint = type === 'google' ? 'google-merchant' : 'meta-csv';
        const filename = type === 'google' ? 'google_merchant.xml' : 'meta_feed.csv';
        
        try {
            const response = await fetch(`${this.apiUrl}/export/${endpoint}/${batchId}`);
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            this.showError('Export failed: ' + error.message);
        }
    }

    downloadTemplate() {
        const csvContent = 'id,title,description,price,category,brand,currency,sku,color,size,material\n' +
                          'prod-001,"Sample Product","Sample description",99.99,"Electronics","SampleBrand","USD","SKU-001","Black","Large","Plastic"';
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'product_template.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    }

    updateDashboard() {
        const totalProducts = this.batchResults.reduce((sum, batch) => sum + batch.summary.total_products, 0);
        const totalOptimized = this.batchResults.reduce((sum, batch) => sum + batch.summary.successful, 0);
        const avgScore = this.batchResults.length > 0 
            ? this.batchResults.reduce((sum, batch) => sum + batch.summary.average_score, 0) / this.batchResults.length 
            : 0;

        document.getElementById('total-products').textContent = totalProducts.toLocaleString();
        document.getElementById('optimized-products').textContent = totalOptimized.toLocaleString();
        document.getElementById('average-score').textContent = Math.round(avgScore * 100) + '%';
        document.getElementById('total-batches').textContent = this.batchResults.length;

        // Update batches list
        const batchesList = document.getElementById('batches-list');
        if (this.batchResults.length === 0) {
            batchesList.innerHTML = '<p class="empty-state">No batches yet. Start optimizing products!</p>';
        } else {
            batchesList.innerHTML = this.batchResults.map(batch => `
                <div class="batch-item" style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <h4>Batch ${batch.batch_id.slice(-8)}</h4>
                    <p>Products: ${batch.summary.total_products} | Success: ${batch.summary.successful} | Score: ${Math.round(batch.summary.average_score * 100)}%</p>
                </div>
            `).join('');
        }
    }

    showLoading() {
        document.getElementById('loading').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }

    showError(message) {
        document.getElementById('error-text').textContent = message;
        document.getElementById('error-message').classList.remove('hidden');
    }

    hideError() {
        document.getElementById('error-message').classList.add('hidden');
    }
}

// Initialize the app
const aiOptimizer = new AIOptimizer();
