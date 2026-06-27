// Setup Chart.js global visualization defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Segoe UI', sans-serif";

const maxPoints = 60;
const initialData = Array(maxPoints).fill(0);
const labels = Array(maxPoints).fill('');

const chartConfig = (color) => ({
    type: 'line',
    data: {
        labels: [...labels],
        datasets: [{
            data: [...initialData],
            borderColor: color,
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 0
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: { x: { display: false }, y: { display: false, min: 0 } },
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        layout: { padding: 0 }
    }
});

// Initialize Line Canvas Charts
const chartThroughput = new Chart(document.getElementById('chart-throughput').getContext('2d'), chartConfig('#38bdf8')); // Sky Blue
const chartQueue = new Chart(document.getElementById('chart-queue').getContext('2d'), chartConfig('#818cf8')); // Indigo Indigo

// Explicit DOM Element Caching
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const elThroughput = document.getElementById('val-throughput');
const elQueue = document.getElementById('val-queue');
const elDrops = document.getElementById('val-drops');
const elAlerts = document.getElementById('val-alerts');
const cardDrops = document.getElementById('card-drops');
const deskContent = document.getElementById('diagnostic-content');
const defaultDeskMsg = document.getElementById('diagnostic-default');

function updateChart(chart, newValue) {
    const dataArr = chart.data.datasets[0].data;
    dataArr.push(newValue);
    dataArr.shift();
    chart.update();
}

function connectWebSocket() {
    const ws = new WebSocket("ws://localhost:8000");

    ws.onopen = () => {
        statusDot.classList.add('connected');
        statusText.innerText = "Live Streaming";
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Update Text Telemetry Nodes
        elThroughput.innerText = data.throughput.toLocaleString();
        elQueue.innerText = data.queue_depth.toLocaleString();
        elDrops.innerText = data.total_drops.toLocaleString();
        elAlerts.innerText = data.total_alerts.toLocaleString();

        // Update Rolling Timeline Canvas Waves
        updateChart(chartThroughput, data.throughput);
        updateChart(chartQueue, data.queue_depth);

        // Smart Hardware Alarms (Pulse if data loss detected)
        if (data.total_drops > 0) {
            cardDrops.classList.add('pulse-danger');
        } else {
            cardDrops.classList.remove('pulse-danger');
        }

        // Dynamically Append Streaming Gemini Reports to Console
        if (data.ai_analysis) {
            if (defaultDeskMsg) defaultDeskMsg.style.display = 'none';

            const entry = document.createElement('div');
            entry.className = 'log-entry';

            const timestamp = document.createElement('div');
            timestamp.className = 'log-timestamp';
            timestamp.innerText = `[${new Date().toLocaleTimeString()}] INCOMING AI DIAGNOSTIC REPORT:`;

            const textNode = document.createTextNode(data.ai_analysis);

            entry.appendChild(timestamp);
            entry.appendChild(textNode);
            deskContent.prepend(entry);
        }
    };

    ws.onclose = () => {
        statusDot.classList.remove('connected');
        statusText.innerText = "Reconnecting...";
        elThroughput.innerText = "0";
        setTimeout(connectWebSocket, 2000); // Backoff retry interval
    };

    ws.onerror = (err) => {
        ws.close();
    };
}

// Boot Client Workspace App
connectWebSocket();