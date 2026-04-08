const API_URL = ""; // Relative if served by same FastAPI

// UI State Management
function showSection(section) {
    const sections = ['analysis-section', 'intel-section', 'portfolio-section', 'compliance-section', 'integrations-section', 'library-section', 'settings-section'];
    sections.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
    
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    
    const activeSection = document.getElementById(`${section}-section`);
    if (activeSection) activeSection.style.display = 'block';
    
    // Find link and make active
    const navItems = {
        'analysis': 0, 'intel': 1, 'portfolio': 2, 'library': 3, 'compliance': 4, 'integrations': 5, 'settings': 6
    };
    const targetIdx = navItems[section];
    if (targetIdx !== undefined) {
        document.querySelectorAll('.nav-item')[targetIdx].classList.add('active');
    }

    if (section === 'library') loadLibrary();
    if (section === 'settings') loadSettings();
}

// File Upload Logic
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const processBtn = document.getElementById('process-btn');

dropzone.onclick = () => fileInput.click();

fileInput.onchange = (e) => {
    const files = e.target.files;
    dropzone.querySelector('p').innerText = `${files.length} file(s) selected`;
};

processBtn.onclick = async () => {
    const files = fileInput.files;

    if (files.length === 0) {
        alert("Please select at least one file to process.");
        return;
    }

    // Auto-derive company name from filename
    const company = files[0].name.split('.')[0].replace(/[-_]/g, ' ');

    processBtn.disabled = true;
    processBtn.innerText = "Processing deal flow...";
    
    const formData = new FormData();
    formData.append('company', company);
    for (let file of files) {
        formData.append('files', file);
    }

    try {
        const targetUrl = `${API_URL}/email-webhook`;
        console.log(`🚀 Dispatching Analysis to: ${targetUrl}`);
        const response = await fetch(targetUrl, {
            method: 'POST',
            body: formData
        });

        const text = await response.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (parseError) {
            console.error("Malformed Response:", text);
            throw new Error(`Server returned invalid JSON: ${text.substring(0, 50)}...`);
        }

        if (data.status === "error") {
            alert(`Analysis Error: ${data.message}`);
        } else {
            renderAnalysis(data);
        }
    } catch (err) {
        console.error(err);
        alert(`Processing failed: ${err.message}`);
    } finally {
        processBtn.disabled = false;
        processBtn.innerText = "Analyse Data & Generate Drafts";
    }
};
function renderAnalysis(data) {
    const analysisBox = document.getElementById('analysis-markdown');
    const emailBox = document.getElementById('email-draft');
    
    // Markdown rendering
    analysisBox.innerHTML = `<h3>Report Summary</h3><p>${data.analysis.replace(/\n/g, '<br>')}</p>`;
    emailBox.innerText = data.draft_email;
    
    // Update Chart
    if (data.revenue_data && data.revenue_data.length > 0) {
        const labels = data.revenue_data.map(r => r.year);
        const revenues = data.revenue_data.map(r => r.revenue);
        updateRevenueChart(labels, revenues);

        const snapshot = document.getElementById('deal-snapshot');
        snapshot.innerHTML = `
            <div style="margin-top:1rem;">
                <p><strong>Revenue Trajectory:</strong></p>
                <h3 style="color:var(--accent-success)">$${(revenues[revenues.length-1]/1000000).toFixed(1)}M</h3>
                <p style="font-size:0.8rem; color:var(--text-muted);">Projected by ${labels[labels.length-1]}</p>
            </div>
        `;
    }
}

// Global Search (RAG)
const searchInput = document.getElementById('global-search');
searchInput.onkeypress = async (e) => {
    if (e.key === 'Enter') {
        const query = searchInput.value;
        const symMatch = query.match(/\$([A-Z]+)/);
        const symbol = symMatch ? symMatch[1] : "";
        
        searchInput.disabled = true;
        
        try {
            const response = await fetch(`${API_URL}/query?q=${encodeURIComponent(query)}&symbol=${symbol}`);
            const data = await response.json();
            renderIntel(data);
            showSection('intel');
        } catch (err) {
            console.error(err);
        } finally {
            searchInput.disabled = false;
        }
    }
};

function renderIntel(data) {
    const resultsContainer = document.getElementById('search-results');
    
    let html = `
        <div style="background: rgba(99, 102, 241, 0.1); padding:1.5rem; border-radius:12px; margin-bottom:2rem; border-left:4px solid var(--primary);">
            <h3 style="color:var(--primary); margin-bottom:0.5rem;">AI Insight</h3>
            <p>${data.analysis}</p>
        </div>
    `;

    if (data.projections && data.projections.length > 0) {
        html += `<h4>Financial Memory Found</h4><div style="display:flex; gap:1rem; margin:1rem 0;">`;
        data.projections.forEach(p => {
            html += `<div class="card" style="padding:1rem; border:1px solid #333;">
                <div style="font-size:0.8rem; color:var(--text-muted);">${p.period}</div>
                <div style="font-weight:bold; color:var(--primary);">${p.value}</div>
                <div style="font-size:0.75rem;">${p.metric}</div>
            </div>`;
        });
        html += `</div>`;
    }

    html += `<h4>Corpus Search Results</h4><div style="margin-top:1rem;">`;
    data.results.forEach(res => {
        html += `
            <div style="margin-bottom:1.5rem; border-bottom:1px solid #222; padding-bottom:1rem;">
                <div style="color:var(--secondary); font-size:0.8rem; font-weight:bold;">Source: ${res.type}</div>
                <div style="font-size:0.9rem; color:var(--text-muted);">${res.text.substring(0, 300)}...</div>
            </div>
        `;
    });
    html += `</div>`;
    
    resultsContainer.innerHTML = html;
}

// Chart Initializers
let revenueChart;
function updateRevenueChart(labels, data) {
    const ctx = document.getElementById('revenueChart').getContext('2d');
    if (revenueChart) revenueChart.destroy();
    
    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'ARR Projection ($)',
                data: data,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { grid: { color: '#222' }, ticks: { color: '#94a3b8' } },
                x: { grid: { color: '#222' }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// Market Ingest Logic
async function ingestMarketData() {
    const ticker = document.getElementById('ingest-ticker').value;
    const status = document.getElementById('ingest-status');
    if (!ticker) return;

    status.innerText = "⏳ Ingesting SEC Edgar & Yahoo Data...";
    
    try {
        const response = await fetch(`${API_URL}/fin-ingest?symbol=${ticker}`, { method: 'POST' });
        const data = await response.json();
        status.innerText = `✅ Ingested ${data.results.length} document chunks for ${ticker}`;
    } catch (err) {
        status.innerText = "❌ Ingest failed.";
    }
}

// Portfolio Benchmark Mock Chart
window.onload = () => {
    const ctx = document.getElementById('benchChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['SaaS', 'Fintech', 'Hardware', 'BioTech'],
            datasets: [{
                data: [40, 25, 20, 15],
                backgroundColor: ['#6366f1', '#ec4899', '#10b981', '#f59e0b'],
                borderWidth: 0
            }]
        },
        options: {
            plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } }
        }
    });
};

// Library Management
function loadLibrary() {
    const tbody = document.getElementById('library-tbody');
    // Simulated data for now, ideally fetch from backend
    const mockDecks = [
        { name: "Pitchdeck_Target", date: "2026-04-08", confidence: "98%", file: "Pitchdeck.pdf" },
        { name: "EcoLogistics_SeriesA", date: "2026-04-07", confidence: "94%", file: "ecologistics.pdf" },
        { name: "MedTech_PreSeed", date: "2026-04-05", confidence: "99%", file: "medtech_pitch.pdf" }
    ];

    tbody.innerHTML = mockDecks.map(deck => `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
            <td style="padding: 1rem;"><strong>${deck.name}</strong></td>
            <td>${deck.date}</td>
            <td><span class="badge badge-success">${deck.confidence}</span></td>
            <td>
                <button class="nav-item" style="padding: 5px 10px; font-size: 0.7rem; background: #222;" onclick="alert('Viewing ${deck.file}')">View</button>
            </td>
        </tr>
    `).join('');
}

// Settings Management
let systemWatchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"];

function loadSettings() {
    const watchlistDiv = document.getElementById('settings-watchlist');
    if (!watchlistDiv) return;
    watchlistDiv.innerHTML = systemWatchlist.map(sym => `
        <span class="badge" style="background: rgba(99, 102, 241, 0.1); border: 1px solid var(--primary); display: flex; align-items: center; gap: 5px; cursor: default;">
            ${sym} <i data-lucide="x" style="width: 12px; height: 12px; cursor: pointer;" onclick="removeSymbol('${sym}')"></i>
        </span>
    `).join('');
    lucide.createIcons();
}

function addSymbol() {
    const input = document.getElementById('add-watchlist');
    const symbol = input.value.toUpperCase();
    if (symbol && !systemWatchlist.includes(symbol)) {
        systemWatchlist.push(symbol);
        input.value = "";
        loadSettings();
    }
}

function removeSymbol(sym) {
    systemWatchlist = systemWatchlist.filter(s => s !== sym);
    loadSettings();
}
