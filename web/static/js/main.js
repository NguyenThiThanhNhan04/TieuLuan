document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // 1. Navigation & Tab Switching
    // ----------------------------------------------------
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const inputTypeField = document.getElementById('input-type');

    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.tab;
                
                // Toggle active button
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Toggle active content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === `${target}-tab`) {
                        content.classList.add('active');
                    }
                });

                // Update hidden form field
                if (inputTypeField) {
                    inputTypeField.value = target;
                }
            });
        });
    }

    // ----------------------------------------------------
    // 2. Drag & Drop File Upload
    // ----------------------------------------------------
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('selected-file-info');

    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', () => fileInput.click());

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--primary)';
            uploadZone.style.background = 'rgba(99, 102, 241, 0.05)';
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = 'var(--border-color)';
                uploadZone.style.background = 'rgba(255, 255, 255, 0.01)';
            });
        });

        uploadZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateFileInfo(files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                updateFileInfo(fileInput.files[0]);
            }
        });
    }

    function updateFileInfo(file) {
        if (fileInfo) {
            fileInfo.innerHTML = `📄 <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)`;
            fileInfo.style.display = 'inline-flex';
        }
    }

    // ----------------------------------------------------
    // 3. API Submission & Results Rendering
    // ----------------------------------------------------
    const predictForm = document.getElementById('predict-form');
    const loadingContainer = document.getElementById('loading-container');
    const resultsContainer = document.getElementById('results-container');
    const initialPrompt = document.getElementById('initial-prompt');

    if (predictForm) {
        predictForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Hide previous results & show loading
            if (resultsContainer) resultsContainer.style.display = 'none';
            if (initialPrompt) initialPrompt.style.display = 'none';
            if (loadingContainer) loadingContainer.style.display = 'flex';
            
            const formData = new FormData(predictForm);
            
            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (loadingContainer) loadingContainer.style.display = 'none';
                
                if (result.status === 'success') {
                    renderResults(result.data);
                    
                    // Save to local storage history
                    if (result.data.history_record) {
                        const history = loadLocalHistory();
                        history.unshift(result.data.history_record);
                        if (history.length > 500) history.pop(); // Keep max 500 records
                        saveLocalHistory(history);
                    }
                } else {
                    showError(result.message || 'Đã xảy ra lỗi không xác định.');
                }
            } catch (error) {
                if (loadingContainer) loadingContainer.style.display = 'none';
                showError('Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại backend Flask.');
                console.error(error);
            }
        });
    }

    function showError(message) {
        if (initialPrompt) {
            initialPrompt.style.display = 'block';
            initialPrompt.innerHTML = `
                <div class="glass-panel" style="padding: 2rem; text-align: center; border-color: var(--fake);">
                    <span style="font-size: 2.5rem; color: var(--fake);">⚠️</span>
                    <h3 style="margin: 1rem 0; font-family: 'Outfit';">Lỗi Phân Tích</h3>
                    <p style="color: var(--text-secondary); line-height: 1.5;">${message}</p>
                </div>
            `;
        }
    }

    function renderResults(data) {
        if (!resultsContainer) return;
        
        // Show container
        resultsContainer.style.display = 'block';
        resultsContainer.scrollIntoView({ behavior: 'smooth' });

        // Update Title & Source
        document.getElementById('res-title').textContent = data.title;
        document.getElementById('res-source-name').textContent = data.source.name;
        document.getElementById('res-source-trust').textContent = `Độ tin cậy nguồn: ${data.source.trust}% (${data.source.label})`;
        
        // Update Prediction Badge
        const badge = document.getElementById('res-badge');
        badge.className = 'result-badge';
        if (data.prediction === 'REAL') {
            badge.classList.add('real');
            badge.textContent = data.language === 'vi' ? 'TIN THẬT' : 'REAL NEWS';
        } else {
            badge.classList.add('fake');
            badge.textContent = data.language === 'vi' ? 'TIN GIẢ' : 'FAKE NEWS';
        }

        // Draw Gauge SVG
        drawGauge(data.confidence, data.prediction === 'REAL' ? 'var(--real)' : 'var(--fake)');

        // Model Information Footer
        document.getElementById('res-model-used').textContent = data.model_used;
        document.getElementById('res-lang').textContent = data.language.toUpperCase();

        // Sentiment Metric
        const sentimentVal = document.getElementById('res-sentiment-value');
        sentimentVal.textContent = data.sentiment.label;
        sentimentVal.className = 'metric-value';
        if (data.sentiment.label.includes('Tích cực') || data.sentiment.label.includes('Positive')) {
            sentimentVal.classList.add('sentiment-positive');
        } else if (data.sentiment.label.includes('Tiêu cực') || data.sentiment.label.includes('Negative')) {
            sentimentVal.classList.add('sentiment-negative');
        } else {
            sentimentVal.classList.add('sentiment-neutral');
        }

        // Clickbait Metric
        const clickbaitVal = document.getElementById('res-clickbait-value');
        clickbaitVal.textContent = `${data.clickbait.score}/100`;
        clickbaitVal.className = 'metric-value';
        if (data.clickbait.score > 60) {
            clickbaitVal.classList.add('clickbait-high');
        } else if (data.clickbait.score > 25) {
            clickbaitVal.classList.add('clickbait-medium');
        } else {
            clickbaitVal.classList.add('clickbait-low');
        }

        // Clickbait factors list
        const factorList = document.getElementById('res-clickbait-factors');
        factorList.innerHTML = '';
        if (data.clickbait.factors && data.clickbait.factors.length > 0) {
            data.clickbait.factors.forEach(factor => {
                const li = document.createElement('li');
                li.textContent = factor;
                factorList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = data.language === 'vi' ? 'Không phát hiện yếu tố giật tít.' : 'No clickbait elements detected.';
            factorList.appendChild(li);
        }

        // Explanation text
        document.getElementById('res-explanation').innerHTML = `<p>${data.explanation}</p>`;

        // Highlighted Content
        document.getElementById('res-highlighted-content').innerHTML = data.highlighted_content;
    }

    function drawGauge(score, color) {
        const valueEl = document.getElementById('res-confidence-value');
        if (valueEl) {
            valueEl.textContent = `${score.toFixed(1)}%`;
        }

        const circle = document.getElementById('gauge-circle-progress');
        if (circle) {
            // Circle radius is 50, circumference is 2 * PI * r = 314.16
            // We want to animate the stroke-dashoffset
            const radius = 50;
            const circumference = 2 * Math.PI * radius;
            
            circle.style.strokeDasharray = circumference;
            // map score (0-100) to dashoffset (circumference to 0)
            const offset = circumference - (score / 100) * circumference;
            
            circle.style.stroke = color;
            circle.style.strokeDashoffset = offset;
            
            // Add custom style drop-shadow glow
            circle.style.filter = `drop-shadow(0px 0px 6px ${color})`;
        }
    }

    // ----------------------------------------------------
    // 4. Local Storage History Management
    // ----------------------------------------------------
    const HISTORY_KEY = 'fakeNewsHistory';
    
    function loadLocalHistory() {
        try {
            const raw = localStorage.getItem(HISTORY_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            console.error("Error reading history from local storage", e);
            return [];
        }
    }
    
    function saveLocalHistory(history) {
        try {
            localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
            // Trigger dashboard reload if we are on dashboard tab
            if (document.getElementById('dashboard-tab').classList.contains('active')) {
                initDashboard();
            }
        } catch (e) {
            console.error("Error saving history to local storage", e);
        }
    }

    // Initialize Dashboard when clicking on its tab
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === 'dashboard') {
            btn.addEventListener('click', () => {
                initDashboard();
            });
        }
    });

    // ----------------------------------------------------
    // 5. Dashboard Statistics & Charts
    // ----------------------------------------------------
    const dashboardStats = document.getElementById('dashboard-stats-page');
    if (dashboardStats) {
        initDashboard();
    }

    async function initDashboard() {
        try {
            const history = loadLocalHistory();
            const total_checks = history.length;
            
            let fake_count = 0;
            let real_count = 0;
            let time_series = {};
            
            history.forEach(h => {
                if (h.prediction === 'FAKE') fake_count++;
                else real_count++;
                
                const date_str = h.timestamp ? h.timestamp.substring(0, 10) : '';
                if (date_str) {
                    if (!time_series[date_str]) {
                        time_series[date_str] = { real: 0, fake: 0 };
                    }
                    if (h.prediction === 'FAKE') time_series[date_str].fake++;
                    else time_series[date_str].real++;
                }
            });
            
            const fake_rate = total_checks > 0 ? ((fake_count / total_checks) * 100).toFixed(1) : 0;
            
            const dates = Object.keys(time_series).sort();
            const real_trends = dates.map(d => time_series[d].real);
            const fake_trends = dates.map(d => time_series[d].fake);
            
            const data = {
                total_checks,
                fake_count,
                real_count,
                fake_rate,
                trends: { dates, real: real_trends, fake: fake_trends },
                recent_history: history.slice(0, 20)
            };
            
            // 1. Render numeric metrics
            document.getElementById('stat-total-checks').textContent = data.total_checks.toLocaleString();
            document.getElementById('stat-fake-rate').textContent = `${data.fake_rate}%`;
            document.getElementById('stat-real-count').textContent = data.real_count.toLocaleString();
            document.getElementById('stat-fake-count').textContent = data.fake_count.toLocaleString();
            
            // 2. Render charts
            renderCharts(data);
            
            // 3. Populate history table
            populateHistoryTable(data.recent_history);
            
        } catch (error) {
            console.error('Lỗi khi tải dữ liệu thống kê:', error);
        }
    }

    function renderCharts(data) {
        const doughnutCtx = document.getElementById('ratioChart').getContext('2d');
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        
        if (window.ratioChartInstance) window.ratioChartInstance.destroy();
        if (window.trendChartInstance) window.trendChartInstance.destroy();
        
        // Real vs Fake ratio doughnut
        window.ratioChartInstance = new Chart(doughnutCtx, {
            type: 'doughnut',
            data: {
                labels: ['Tin Thật (Real)', 'Tin Giả (Fake)'],
                datasets: [{
                    data: [data.real_count, data.fake_count],
                    backgroundColor: ['#10b981', '#f43f5e'],
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#1e293b',
                            font: { family: 'Inter', size: 12, weight: '500' }
                        }
                    }
                },
                cutout: '72%'
            }
        });

        // Verification trends line chart
        const trends = data.trends || { dates: [], real: [], fake: [] };
        
        window.trendChartInstance = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: trends.dates,
                datasets: [
                    {
                        label: 'Tin Thật',
                        data: trends.real,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.06)',
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2.5
                    },
                    {
                        label: 'Tin Giả',
                        data: trends.fake,
                        borderColor: '#f43f5e',
                        backgroundColor: 'rgba(244, 63, 94, 0.06)',
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2.5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#1e293b',
                            font: { family: 'Inter', size: 12, weight: '500' }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(0, 0, 0, 0.04)' },
                        ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } }
                    },
                    y: {
                        grid: { color: 'rgba(0, 0, 0, 0.04)' },
                        ticks: { color: '#64748b', stepSize: 1 }
                    }
                }
            }
        });
    }

    function populateHistoryTable(historyList) {
        const tbody = document.getElementById('history-table-body');
        const emptyPlaceholder = document.getElementById('table-empty-placeholder');
        
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (!historyList || historyList.length === 0) {
            if (emptyPlaceholder) emptyPlaceholder.style.display = 'block';
            return;
        }
        
        if (emptyPlaceholder) emptyPlaceholder.style.display = 'none';

        historyList.forEach(item => {
            const tr = document.createElement('tr');
            
            // Format timestamp nicely
            const date = new Date(item.timestamp);
            const formattedDate = isNaN(date.getTime()) 
                ? item.timestamp 
                : `${date.getDate()}/${date.getMonth() + 1} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

            const badgeClass = item.prediction === 'REAL' ? 'real' : 'fake';
            const badgeText = item.prediction === 'REAL' ? 'Thật' : 'Giả';

            tr.innerHTML = `
                <td><span class="badge-lang">${item.language}</span></td>
                <td>
                    <div style="font-weight: 500; color: var(--text-primary); max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.title}">
                        ${item.title}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${item.content_snippet}
                    </div>
                </td>
                <td><span class="badge-status ${badgeClass}">${badgeText}</span></td>
                <td style="font-weight: 600;">${item.confidence.toFixed(1)}%</td>
                <td><span style="font-size: 0.8rem; color: var(--text-secondary);">${item.source}</span></td>
                <td><span style="font-size: 0.8rem; color: var(--text-muted);">${item.model_used}</span></td>
                <td><span style="font-size: 0.85rem; color: var(--text-secondary);">${formattedDate}</span></td>
            `;
            
            tbody.appendChild(tr);
        });
    }
});
