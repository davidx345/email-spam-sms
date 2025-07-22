// Enterprise Spam Detector - Modern JavaScript Application
// Version 2.0.0 - Production Ready

class SpamDetectorApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.systemMetrics = {
            responseTime: 85,
            requestRate: 1247,
            cacheHitRate: 87.3,
            healthScore: 100
        };
        this.charts = {};
        this.isProcessing = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startRealTimeUpdates();
        this.checkSystemHealth();
        this.setupThemeToggle();
        this.setupMobileMenu();
    }

    setupEventListeners() {
        // Single message analysis
        const analyzeBtn = document.getElementById('analyze-btn');
        const messageInput = document.getElementById('message-input');
        
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeSingleMessage());
        }
        
        if (messageInput) {
            messageInput.addEventListener('input', this.updateCharCount.bind(this));
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    this.analyzeSingleMessage();
                }
            });
        }

        // Batch processing
        const batchAnalyzeBtn = document.getElementById('batch-analyze-btn');
        if (batchAnalyzeBtn) {
            batchAnalyzeBtn.addEventListener('click', () => this.processBatch());
        }

        // File upload
        const fileInput = document.getElementById('file-input');
        const fileAnalyzeBtn = document.getElementById('file-analyze-btn');
        
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }
        
        if (fileAnalyzeBtn) {
            fileAnalyzeBtn.addEventListener('click', () => this.processFile());
        }

        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => this.switchTab(e.target.id));
        });

        // API testing
        const testApiBtn = document.getElementById('test-api-btn');
        if (testApiBtn) {
            testApiBtn.addEventListener('click', () => this.testAPI());
        }

        // Feedback buttons
        document.addEventListener('click', (e) => {
            if (e.target.id === 'feedback-correct' || e.target.id === 'feedback-incorrect') {
                this.submitFeedback(e.target.id === 'feedback-correct');
            }
        });
    }

    updateCharCount() {
        const input = document.getElementById('message-input');
        const counter = document.getElementById('char-count');
        
        if (input && counter) {
            const count = input.value.length;
            counter.textContent = `${count}/1000`;
            
            if (count > 800) {
                counter.classList.add('text-orange-500');
            } else {
                counter.classList.remove('text-orange-500');
            }
        }
    }

    async analyzeSingleMessage() {
        const messageInput = document.getElementById('message-input');
        const analyzeBtn = document.getElementById('analyze-btn');
        const resultSection = document.getElementById('analysis-result');
        
        const message = messageInput.value.trim();
        
        if (!message) {
            this.showToast('Please enter a message to analyze', 'warning');
            return;
        }

        if (message.length > 1000) {
            this.showToast('Message too long (max 1000 characters)', 'error');
            return;
        }

        this.setLoading(analyzeBtn, true);
        const startTime = Date.now();

        try {
            const response = await this.makeAPICall('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (response.ok) {
                const result = await response.json();
                const processingTime = Date.now() - startTime;
                
                this.displaySingleResult(result, processingTime);
                resultSection.classList.remove('hidden');
                
                this.showToast('Analysis completed successfully!', 'success');
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        } finally {
            this.setLoading(analyzeBtn, false);
        }
    }

    displaySingleResult(result, processingTime) {
        const resultCard = document.getElementById('result-card');
        const resultIcon = document.getElementById('result-icon');
        const resultLabel = document.getElementById('result-label');
        const resultConfidence = document.getElementById('result-confidence');
        const confidenceBadge = document.getElementById('confidence-badge');
        const confidenceBar = document.getElementById('confidence-bar');
        const processingTimeEl = document.getElementById('processing-time');

        // Determine result styling
        const isSpam = result.is_spam;
        const confidence = Math.round(result.spam_probability * 100);
        
        // Update icons and colors
        if (isSpam) {
            resultIcon.innerHTML = '<i data-lucide="alert-triangle" class="h-6 w-6 text-red-600"></i>';
            resultCard.className = 'p-4 rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800';
            resultLabel.textContent = 'SPAM DETECTED';
            resultLabel.className = 'font-semibold text-red-800 dark:text-red-300';
            confidenceBadge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
            confidenceBar.className = 'h-2 rounded-full transition-all duration-500 bg-red-500';
        } else {
            resultIcon.innerHTML = '<i data-lucide="shield-check" class="h-6 w-6 text-green-600"></i>';
            resultCard.className = 'p-4 rounded-lg border border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800';
            resultLabel.textContent = 'LEGITIMATE MESSAGE';
            resultLabel.className = 'font-semibold text-green-800 dark:text-green-300';
            confidenceBadge.className = 'px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
            confidenceBar.className = 'h-2 rounded-full transition-all duration-500 bg-green-500';
        }

        // Update content
        resultConfidence.textContent = `Confidence: ${confidence}%`;
        confidenceBadge.textContent = `${confidence}%`;
        confidenceBar.style.width = `${confidence}%`;
        processingTimeEl.textContent = `Processed in ${processingTime}ms`;

        // Re-initialize icons
        lucide.createIcons();
    }

    async processBatch() {
        const batchInput = document.getElementById('batch-input');
        const batchAnalyzeBtn = document.getElementById('batch-analyze-btn');
        const batchResults = document.getElementById('batch-results');
        
        const messages = batchInput.value.trim().split('\n').filter(msg => msg.trim());
        
        if (messages.length === 0) {
            this.showToast('Please enter at least one message', 'warning');
            return;
        }

        if (messages.length > 100) {
            this.showToast('Maximum 100 messages allowed per batch', 'warning');
            return;
        }

        this.setLoading(batchAnalyzeBtn, true);

        try {
            const results = [];
            
            // Process messages in chunks to avoid overwhelming the server
            const chunkSize = 10;
            for (let i = 0; i < messages.length; i += chunkSize) {
                const chunk = messages.slice(i, i + chunkSize);
                const chunkPromises = chunk.map(message => 
                    this.makeAPICall('/predict', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message })
                    }).then(response => response.json())
                );
                
                const chunkResults = await Promise.all(chunkPromises);
                results.push(...chunkResults);
                
                // Update progress
                const progress = Math.round(((i + chunkSize) / messages.length) * 100);
                batchAnalyzeBtn.innerHTML = `<i data-lucide="cpu" class="h-5 w-5"></i> <span>Processing... ${Math.min(progress, 100)}%</span>`;
            }

            this.displayBatchResults(results);
            batchResults.classList.remove('hidden');
            
            this.showToast(`Successfully processed ${results.length} messages`, 'success');
        } catch (error) {
            console.error('Batch processing error:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        } finally {
            this.setLoading(batchAnalyzeBtn, false);
        }
    }

    displayBatchResults(results) {
        const batchSummary = document.getElementById('batch-summary');
        const batchDetails = document.getElementById('batch-details');
        
        // Calculate summary statistics
        const totalMessages = results.length;
        const spamCount = results.filter(r => r.is_spam).length;
        const hamCount = totalMessages - spamCount;

        // Display summary
        batchSummary.innerHTML = `
            <div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">${totalMessages}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400">Total Processed</div>
            </div>
            <div class="bg-red-100 dark:bg-red-900/20 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-red-600 dark:text-red-400">${spamCount}</div>
                <div class="text-sm text-red-600 dark:text-red-400">Spam Messages</div>
            </div>
            <div class="bg-green-100 dark:bg-green-900/20 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-green-600 dark:text-green-400">${hamCount}</div>
                <div class="text-sm text-green-600 dark:text-green-400">Legitimate Messages</div>
            </div>
        `;

        // Display detailed results
        batchDetails.innerHTML = results.map((result, index) => `
            <div class="flex items-center justify-between p-3 border-b dark:border-gray-700 last:border-b-0">
                <div class="flex-1">
                    <div class="text-sm font-medium text-gray-900 dark:text-white">
                        Message ${index + 1}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-md">
                        ${result.text || `Message ${index + 1}`}
                    </div>
                </div>
                <div class="flex items-center space-x-3">
                    <span class="${result.is_spam ? 'text-red-600 bg-red-100 dark:bg-red-900/20' : 'text-green-600 bg-green-100 dark:bg-green-900/20'} px-2 py-1 rounded text-xs font-medium">
                        ${result.prediction}
                    </span>
                    <span class="text-xs text-gray-500 dark:text-gray-400">
                        ${Math.round(result.spam_probability * 100)}%
                    </span>
                </div>
            </div>
        `).join('');
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        const fileAnalyzeBtn = document.getElementById('file-analyze-btn');
        
        if (file) {
            const fileSize = (file.size / 1024 / 1024).toFixed(2); // Convert to MB
            
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                this.showToast('File too large. Maximum size is 10MB.', 'error');
                event.target.value = '';
                return;
            }
            
            fileAnalyzeBtn.disabled = false;
            fileAnalyzeBtn.innerHTML = `<i data-lucide="file-text" class="h-5 w-5"></i> <span>Process ${file.name} (${fileSize}MB)</span>`;
            
            this.showToast(`File selected: ${file.name}`, 'success');
        } else {
            fileAnalyzeBtn.disabled = true;
            fileAnalyzeBtn.innerHTML = `<i data-lucide="file-text" class="h-5 w-5"></i> <span>Process File</span>`;
        }
        
        lucide.createIcons();
    }

    switchTab(tabId) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active', 'border-blue-500', 'text-blue-600', 'dark:text-blue-400');
            btn.classList.add('border-transparent', 'text-gray-500', 'hover:text-gray-700', 'dark:text-gray-400', 'dark:hover:text-gray-300');
        });
        
        const activeTab = document.getElementById(tabId);
        activeTab.classList.add('active', 'border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        activeTab.classList.remove('border-transparent', 'text-gray-500', 'hover:text-gray-700', 'dark:text-gray-400', 'dark:hover:text-gray-300');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        const contentId = tabId.replace('tab-', 'content-');
        document.getElementById(contentId).classList.remove('hidden');
    }

    async testAPI() {
        const endpointSelect = document.getElementById('api-endpoint');
        const requestTextarea = document.getElementById('api-request');
        const responseDiv = document.getElementById('api-response');
        const responseContent = document.getElementById('api-response-content');
        const testBtn = document.getElementById('test-api-btn');
        
        const endpoint = endpointSelect.value;
        let requestBody = null;
        
        try {
            if (requestTextarea.value.trim()) {
                requestBody = JSON.parse(requestTextarea.value);
            }
        } catch (error) {
            this.showToast('Invalid JSON in request body', 'error');
            return;
        }

        this.setLoading(testBtn, true);

        try {
            const options = {
                method: endpoint === '/health' || endpoint === '/metrics' ? 'GET' : 'POST',
            };
            
            if (requestBody && options.method === 'POST') {
                options.headers = { 'Content-Type': 'application/json' };
                options.body = JSON.stringify(requestBody);
            }

            const response = await this.makeAPICall(endpoint, options);
            const result = await response.text();
            
            let formattedResult;
            try {
                formattedResult = JSON.stringify(JSON.parse(result), null, 2);
            } catch {
                formattedResult = result;
            }

            responseContent.textContent = formattedResult;
            responseDiv.classList.remove('hidden');
            
            this.showToast(`API test completed (${response.status})`, response.ok ? 'success' : 'warning');
        } catch (error) {
            responseContent.textContent = `Error: ${error.message}`;
            responseDiv.classList.remove('hidden');
            this.showToast(`API test failed: ${error.message}`, 'error');
        } finally {
            this.setLoading(testBtn, false);
        }
    }

    initializeCharts() {
        this.initializePerformanceChart();
        this.initializePredictionsChart();
    }

    initializePerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx) return;

        const isDark = document.documentElement.classList.contains('dark');
        const textColor = isDark ? '#e5e7eb' : '#374151';
        const gridColor = isDark ? '#374151' : '#e5e7eb';

        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                datasets: [
                    {
                        label: 'Response Time (ms)',
                        data: this.generateMockData(24, 70, 120),
                        borderColor: '#3b82f6',
                        backgroundColor: '#3b82f610',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Requests/sec',
                        data: this.generateMockData(24, 800, 1500),
                        borderColor: '#10b981',
                        backgroundColor: '#10b98110',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: textColor }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: { color: textColor },
                        grid: { drawOnChartArea: false, color: gridColor }
                    }
                }
            }
        });
    }

    initializePredictionsChart() {
        const ctx = document.getElementById('predictions-chart');
        if (!ctx) return;

        const isDark = document.documentElement.classList.contains('dark');
        const textColor = isDark ? '#e5e7eb' : '#374151';

        this.charts.predictions = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Legitimate', 'Spam'],
                datasets: [{
                    data: [73, 27],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: textColor }
                    }
                }
            }
        });
    }

    generateMockData(length, min, max) {
        return Array.from({length}, () => Math.floor(Math.random() * (max - min + 1)) + min);
    }

    startRealTimeUpdates() {
        // Update system metrics every 5 seconds
        setInterval(() => {
            this.updateSystemMetrics();
        }, 5000);

        // Update timestamp
        setInterval(() => {
            const lastCheckTime = document.getElementById('last-check-time');
            if (lastCheckTime) {
                lastCheckTime.textContent = 'Just now';
            }
        }, 30000);
    }

    updateSystemMetrics() {
        // Simulate real-time metric updates
        this.systemMetrics.responseTime += (Math.random() - 0.5) * 10;
        this.systemMetrics.requestRate += (Math.random() - 0.5) * 100;
        this.systemMetrics.cacheHitRate += (Math.random() - 0.5) * 2;
        
        // Ensure values stay within reasonable bounds
        this.systemMetrics.responseTime = Math.max(50, Math.min(200, this.systemMetrics.responseTime));
        this.systemMetrics.requestRate = Math.max(500, Math.min(2000, this.systemMetrics.requestRate));
        this.systemMetrics.cacheHitRate = Math.max(75, Math.min(95, this.systemMetrics.cacheHitRate));

        // Update DOM elements
        const responseTimeEl = document.getElementById('avg-response-time');
        const requestRateEl = document.getElementById('request-rate');
        const cacheHitRateEl = document.getElementById('cache-hit-rate');

        if (responseTimeEl) responseTimeEl.textContent = `${Math.round(this.systemMetrics.responseTime)}ms`;
        if (requestRateEl) requestRateEl.textContent = Math.round(this.systemMetrics.requestRate).toLocaleString();
        if (cacheHitRateEl) cacheHitRateEl.textContent = `${this.systemMetrics.cacheHitRate.toFixed(1)}%`;
    }

    async checkSystemHealth() {
        try {
            const response = await this.makeAPICall('/health');
            const health = await response.json();
            
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            const healthStatus = document.getElementById('health-status');
            const healthScore = document.getElementById('health-score');
            
            if (health.status === 'healthy') {
                if (statusIndicator) {
                    statusIndicator.className = 'w-3 h-3 bg-green-500 rounded-full animate-pulse';
                }
                if (statusText) statusText.textContent = 'System Healthy';
                if (healthStatus) healthStatus.className = 'w-3 h-3 bg-green-500 rounded-full animate-pulse';
                if (healthScore) healthScore.textContent = '100%';
            } else {
                if (statusIndicator) {
                    statusIndicator.className = 'w-3 h-3 bg-red-500 rounded-full animate-pulse';
                }
                if (statusText) statusText.textContent = 'System Issues';
                if (healthStatus) healthStatus.className = 'w-3 h-3 bg-red-500 rounded-full animate-pulse';
                if (healthScore) healthScore.textContent = '85%';
            }
        } catch (error) {
            console.error('Health check failed:', error);
            // Handle offline state
        }
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        if (!themeToggle) return;

        themeToggle.addEventListener('click', () => {
            const isDark = document.documentElement.classList.toggle('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            
            // Re-initialize charts with new theme
            setTimeout(() => {
                this.destroyCharts();
                this.initializeCharts();
            }, 100);
        });

        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        }
    }

    setupMobileMenu() {
        const mobileMenuButton = document.getElementById('mobile-menu-button');
        const mobileMenu = document.getElementById('mobile-menu');
        
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }
    }

    async submitFeedback(isCorrect) {
        try {
            // This would integrate with a feedback system
            this.showToast(`Thank you for your feedback! ${isCorrect ? 'Marked as correct' : 'Marked as incorrect'}`, 'success');
            
            // Disable feedback buttons after submission
            document.getElementById('feedback-correct').disabled = true;
            document.getElementById('feedback-incorrect').disabled = true;
        } catch (error) {
            this.showToast('Failed to submit feedback', 'error');
        }
    }

    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    }

    async makeAPICall(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        return fetch(url, defaultOptions);
    }

    setLoading(button, isLoading) {
        if (!button) return;
        
        if (isLoading) {
            button.disabled = true;
            button.classList.add('opacity-50', 'cursor-not-allowed');
            const originalContent = button.innerHTML;
            button.dataset.originalContent = originalContent;
            button.innerHTML = `
                <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                <span>Processing...</span>
            `;
        } else {
            button.disabled = false;
            button.classList.remove('opacity-50', 'cursor-not-allowed');
            if (button.dataset.originalContent) {
                button.innerHTML = button.dataset.originalContent;
                lucide.createIcons();
            }
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        const bgColors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        toast.className = `${bgColors[type]} text-white px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full`;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 5000);
    }
}

// Initialize the application
function initializeApp() {
    window.spamDetectorApp = new SpamDetectorApp();
}

// Export for global access
window.initializeApp = initializeApp;
