const socket = io();
let currentRole = null;

// DOM Elements
const roleSelector = document.getElementById('role-selector');
const studentView = document.getElementById('student-view');
const instructorView = document.getElementById('instructor-view');
const connectionStatus = document.getElementById('connection-status');
const feedbackLog = document.getElementById('feedback-log');

// Role Selection
// Role Selection
function selectRole(role) {
    let name = "Instructor"; // Default for instructor

    if (role === 'student') {
        const nameInput = document.getElementById('student-name-input');
        name = nameInput.value.trim();
        if (!name) {
            alert("Please enter your name to join.");
            return;
        }
    }

    currentRole = role;
    roleSelector.classList.add('hidden');

    // Join socket room with Name
    socket.emit('join', { role: role, name: name });

    if (role === 'student') {
        studentView.classList.remove('hidden');
        instructorView.classList.add('hidden');
    } else {
        studentView.classList.add('hidden');
        instructorView.classList.remove('hidden');
        document.body.style.borderTop = "5px solid var(--le-gold)"; // Visual indicator for instructor
        setTimeout(initCharts, 500); // Delay init to ensure DOM visible
        // QR generated on demand now
    }
}

// Socket Events
socket.on('connect', () => {
    connectionStatus.textContent = 'CONNECTED';
    connectionStatus.style.color = '#00FF41';
});

socket.on('disconnect', () => {
    connectionStatus.textContent = 'DISCONNECTED';
    connectionStatus.style.color = 'red';
});

// Charts
let charts = {};

function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    color: '#E5E4E2',
                    font: { size: 14, weight: 'bold' }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 100, /* Fix Y-axis to 100% */
                ticks: {
                    color: '#A0A0A0',
                    callback: function (value) { return value + "%" } /* Add % sign */
                },
                grid: { color: '#333' },
                title: {
                    display: true,
                    text: 'Percentage',
                    color: '#A0A0A0'
                }
            },
            x: {
                border: { display: true, color: '#E5E4E2' },
                ticks: {
                    display: true,
                    color: '#FFFFFF', /* Pure white for max contrast */
                    font: { size: 14, weight: '900' }, /* Extra bold */
                    autoSkip: false,
                    maxRotation: 0, /* Try to keep them flat if possible */
                    padding: 10,
                    z: 10
                },
                grid: { display: false },
                title: {
                    display: true,
                    text: 'Scoring Categories', /* Default Title, overridden per chart if possible */
                    color: '#C5B358', /* Gold for the axis title */
                    font: { size: 16, weight: 'bold' },
                    padding: { top: 10 }
                }
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function (context) {
                        return context.parsed.y + '%';
                    }
                }
            },
            legend: {
                position: 'bottom',
                labels: {
                    color: '#E5E4E2',
                    font: { size: 14, weight: 'bold' }
                }
            }
        }
    };

    // Custom overrides per chart to name the specific axis
    const neuroOptions = JSON.parse(JSON.stringify(commonOptions)); // Deep copy
    // Neuro is a doughnut, no X axis, Y axis usually hidden but let's clear it
    neuroOptions.scales = {};
    neuroOptions.plugins.tooltip = { callbacks: { label: function (context) { return context.parsed + '%'; } } }; // Doughnut uses parsed, not parsed.y

    const owlsOptions = JSON.parse(JSON.stringify(commonOptions));
    owlsOptions.scales.x.title.text = 'OWLS Functions';

    const rftOptions = JSON.parse(JSON.stringify(commonOptions));
    rftOptions.scales.x.title.text = 'Relational Frames';

    const aggOptions = JSON.parse(JSON.stringify(commonOptions));
    aggOptions.scales.x.title.text = 'Intensity Level';

    charts.neuro = new Chart(document.getElementById('chart-neuro'), {
        type: 'doughnut',
        data: { labels: ['Dinosaur', 'Dolphin', 'Human'], datasets: [{ data: [0, 0, 0], backgroundColor: ['#d9534f', '#5bc0de', '#5cb85c'], borderColor: '#002347', borderWidth: 2 }] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { color: '#E5E4E2', font: { size: 14 } } },
                tooltip: { callbacks: { label: function (c) { return c.parsed + '%'; } } }
            }
        }
    });

    charts.owls = new Chart(document.getElementById('chart-owls'), {
        type: 'bar',
        data: { labels: ['Out', 'Watched', 'Locked On', 'Soothing'], datasets: [{ label: 'Percentage', data: [0, 0, 0, 0], backgroundColor: '#C5B358', barPercentage: 0.6 }] },
        options: owlsOptions
    });

    charts.rft = new Chart(document.getElementById('chart-rft'), {
        type: 'bar',
        data: { labels: ['Coordination', 'Deictic', 'Oppositional', 'Temporal', 'Hierarchical'], datasets: [{ label: 'Percentage', data: [0, 0, 0, 0, 0], backgroundColor: '#005A9C', barPercentage: 0.6 }] },
        options: rftOptions
    });

    charts.aggression = new Chart(document.getElementById('chart-aggression'), {
        type: 'bar', // Switch to Bar for clearer labeling
        data: { labels: ['Lvl 1', 'Lvl 2', 'Lvl 3', 'Lvl 4', 'Lvl 5'], datasets: [{ label: 'Percentage', data: [0, 0, 0, 0, 0], backgroundColor: '#d9534f' }] },
        options: aggOptions
    });

    // Trend Graph (Line)
    charts.trend = new Chart(document.getElementById('chart-trend'), {
        type: 'line',
        data: {
            labels: [], // Time points
            datasets: [{
                label: 'Group Reliability (IOA)',
                data: [],
                borderColor: '#00FF41',
                backgroundColor: 'rgba(0, 255, 65, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: '#333' },
                    ticks: { color: '#aaa', callback: function (val) { return val + '%' } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#aaa', maxTicksLimit: 10 }
                }
            },
            plugins: {
                annotation: {
                    annotations: {
                        line1: {
                            type: 'line',
                            yMin: 80,
                            yMax: 80,
                            borderColor: '#C5B358', // Gold
                            borderWidth: 2,
                            borderDash: [10, 5],
                            label: {
                                content: 'Competency Threshold (80%)',
                                enabled: true,
                                position: 'end',
                                backgroundColor: 'rgba(0,0,0,0.5)',
                                color: '#C5B358'
                            }
                        }
                    }
                }
            }
        }
    });
}

// Helper: Calculate Percentages
function calcPercentages(dataObj, labels) {
    let total = 0;
    const values = labels.map(label => dataObj[label] || 0);
    total = values.reduce((a, b) => a + b, 0);

    if (total === 0) return values.map(() => 0);

    return values.map(val => ((val / total) * 100).toFixed(1));
}

// Chart Updates
socket.on('update_charts', (data) => {
    if (currentRole !== 'instructor') return;
    if (!charts.neuro) initCharts();

    // Neuro Brain (Pie)
    const brainData = data.neuro_brain || {};
    charts.neuro.data.datasets[0].data = calcPercentages(brainData, ['Dinosaur', 'Dolphin', 'Human']);
    charts.neuro.update();

    // OWLS (Bar)
    const owlsData = data.owls || {};
    charts.owls.data.datasets[0].data = calcPercentages(owlsData, ['Out', 'Watched', 'Locked On', 'Soothing']);
    charts.owls.update();

    // RFT (Bar)
    const rftData = data.rft || {};
    charts.rft.data.datasets[0].data = calcPercentages(rftData, ['Coordination', 'Deictic', 'Oppositional', 'Temporal', 'Hierarchical']);
    charts.rft.update();

    // Aggression (Line/Bar)
    const aggData = data.neuro_level || {};
    charts.aggression.data.datasets[0].data = calcPercentages(aggData, ['1', '2', '3', '4', '5']);
    charts.aggression.update();

    // Update IOA Display
    const ioa = data.ioa_overall || data.ioa || 0;
    const ioaEl = document.getElementById('ioa-value');
    const ioaBox = document.getElementById('ioa-box');

    if (ioaEl && ioaBox) {
        ioaEl.textContent = ioa + "%";

        if (ioa >= 90) {
            ioaEl.style.color = "#00FF41"; // Matrix Green
            ioaBox.style.borderColor = "#00FF41";
            ioaBox.style.boxShadow = "0 0 10px rgba(0, 255, 65, 0.2)";
        } else {
            ioaEl.style.color = "#ff4444"; // Red
            ioaBox.style.borderColor = "#ff4444";
            ioaBox.style.boxShadow = "none";
        }
    }

    // Helper to update individual IOA indicators
    const updateIoaDisplay = (id, val) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = val + "%";
            el.style.color = val >= 90 ? "#00FF41" : "#ff4444";
        }
    };

    updateIoaDisplay('ioa-neuro', data.ioa_neuro || 0);
    updateIoaDisplay('ioa-aggression', data.ioa_aggression || 0);
    updateIoaDisplay('ioa-owls', data.ioa_owls || 0);
    updateIoaDisplay('ioa-rft', data.ioa_rft || 0);

    // Update Trend Graph
    if (data.ioa_history && charts.trend) {
        // format timestamps to HH:MM:SS
        const history = data.ioa_history;
        charts.trend.data.labels = history.map(h => new Date(h.timestamp * 1000).toLocaleTimeString());
        charts.trend.data.datasets[0].data = history.map(h => h.ioa);

        // Dynamic color based on latest value
        const lastVal = history.length > 0 ? history[history.length - 1].ioa : 0;
        const color = lastVal >= 80 ? '#00FF41' : (lastVal >= 60 ? '#ffea00' : '#ff4444');
        charts.trend.data.datasets[0].borderColor = color;
        charts.trend.data.datasets[0].backgroundColor = color.replace(')', ', 0.1)').replace('rgb', 'rgba'); // Hacky but works for hex too if we convert, but let's stick to hex for border. 
        // Actually, just keep green for success, maybe red for fail. Stick to green for now.

        charts.trend.update();
    }
});

// Metrics Updates
socket.on('update_metrics', (data) => {
    // Note: We update even if not instructor just to see if event fires, though effectively hidden for students
    const activeEl = document.getElementById('metric-active-students');
    const totalEl = document.getElementById('metric-total-responses');

    if (activeEl) activeEl.textContent = data.active_students;
    if (totalEl) totalEl.textContent = data.total_responses;

    // Category Counters
    const cNeuro = document.getElementById('count-neuro');
    const cOwls = document.getElementById('count-owls');
    const cRft = document.getElementById('count-rft');
    const cAgg = document.getElementById('count-aggression');

    if (cNeuro) cNeuro.textContent = data.neuro_count || 0;
    if (cOwls) cOwls.textContent = data.owls_count || 0;
    if (cRft) cRft.textContent = data.rft_count || 0;
    if (cAgg) cAgg.textContent = data.aggression_count || 0;
});

// Controls
function resetSession() {
    if (confirm("Are you sure you want to clear all class data?")) {
        socket.emit('reset_session');
        stopTimer();
    }
}

// Session Controls
let timerInterval;
const timerEl = document.getElementById('session-timer');

function startSession() {
    socket.emit('start_session');
}

function extendSession() {
    // Protor Key Check (simulated for now, or just simple confirm)
    if (confirm("Extend session by 60 minutes?")) {
        socket.emit('extend_session', { minutes: 60 });
    }
}

function downloadReport() {
    // Open in new tab
    window.open('/download_report', '_blank');
}

function startTimer(endTimeSeconds) {
    stopTimer();

    function update() {
        const now = Date.now() / 1000;
        let diff = endTimeSeconds - now;

        if (diff <= 0) {
            diff = 0;
            timerEl.style.color = 'red';
            stopTimer();
        } else {
            timerEl.style.color = '#fff';
        }

        const h = Math.floor(diff / 3600);
        const m = Math.floor((diff % 3600) / 60);
        const s = Math.floor(diff % 60);

        timerEl.textContent =
            (h < 10 ? "0" + h : h) + ":" +
            (m < 10 ? "0" + m : m) + ":" +
            (s < 10 ? "0" + s : s);
    }

    update();
    timerInterval = setInterval(update, 1000);
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
}

// Session Socket Events
socket.on('session_started', (data) => {
    console.log("Session Started", data);
    startTimer(data.end_time);
    // Unlock UI
    document.body.classList.remove('locked-session');
});

socket.on('session_extended', (data) => {
    console.log("Session Extended", data);
    startTimer(data.end_time);
    document.body.classList.remove('locked-session');
});

socket.on('session_locked', (data) => {
    alert("SESSION LOCKED: " + data.msg);
    stopTimer();
    timerEl.textContent = "00:00:00";
    timerEl.style.color = "red";
    document.body.classList.add('locked-session');
});

// QR Code
let qrGenerated = false;

function toggleQR(show) {
    const modal = document.getElementById('qr-modal');
    if (show) {
        modal.classList.remove('hidden');
        generateQR(); // Always regenerate to catch new URLs
    } else {
        modal.classList.add('hidden');
    }
}

function generateQR(forceLocal = false) {
    try {
        let host = (typeof SERVER_IP !== 'undefined' && SERVER_IP && !forceLocal) ? SERVER_IP : LOCAL_IP;
        let url;

        // Determine the full URL
        if (host.startsWith('http')) {
            url = host + (host.includes('?') ? '&' : '?') + 't=' + new Date().getTime();
        } else {
            url = `http://${host}:5001`;
        }

        // Display update
        const displayUrl = url.replace(/^https?:\/\//, '').replace(/\/$/, '');
        document.getElementById('join-url').textContent = displayUrl;

        // Visual distinction for Local vs Public
        const helpText = document.querySelector("#qr-modal p");
        const modalTitle = document.querySelector("#qr-modal h2");
        
        if (host.includes("ngrok") || (typeof PUBLIC_URL !== 'undefined' && host === PUBLIC_URL)) {
            modalTitle.textContent = "Student Access (PUBLIC)";
            modalTitle.style.color = "var(--le-gold)";
            helpText.innerHTML = "⚠️ <b>On phone:</b> Click <b>'Visit Site'</b> to bypass the warning.";
            helpText.style.color = "#ffdd00";
        } else {
            modalTitle.textContent = "Student Access (LOCAL WI-FI)";
            modalTitle.style.color = "var(--le-green)";
            helpText.textContent = "Phone must be on SAME Wi-Fi as this computer.";
            helpText.style.color = "#00FF41";
        }

        // Add a toggle button if not present
        if (!document.getElementById('qr-toggle-btn')) {
            const toggleBtn = document.createElement('button');
            toggleBtn.id = 'qr-toggle-btn';
            toggleBtn.className = 'control-btn';
            toggleBtn.style.margin = "10px";
            toggleBtn.style.background = "#222";
            toggleBtn.style.borderColor = "#666";
            toggleBtn.style.fontSize = "0.7rem";
            toggleBtn.onclick = () => {
                const isCurrentlyLocal = modalTitle.textContent.includes("LOCAL");
                generateQR(!isCurrentlyLocal);
            };
            document.querySelector('.modal-content').insertBefore(toggleBtn, document.querySelector('#qr-modal button:last-child'));
        }
        document.getElementById('qr-toggle-btn').textContent = host.includes("ngrok") ? "SWITCH TO LOCAL WI-FI LINK" : "SWITCH TO PUBLIC LINK";

        // Clear and Draw
        document.getElementById("qrcode").innerHTML = "";
        new QRCode(document.getElementById("qrcode"), {
            text: url,
            width: 256,
            height: 256,
            colorDark: "#002347",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
    } catch (e) {
        console.error(e);
    }
}

// Instructor: Receive Feedback
socket.on('student_feedback', (data) => {
    if (currentRole !== 'instructor') return;

    // Log to console/screen
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    const timestamp = new Date().toLocaleTimeString();
    entry.innerHTML = `<span style="color:#888">[${timestamp}]</span> <strong>${data.category}</strong>: ${data.value}`;
    feedbackLog.prepend(entry);

    // Provide visual feedback (could be a chart update later)
    flashDashboard();
});

function flashDashboard() {
    const dash = document.querySelector('.dashboard-grid');
    if (dash) {
        dash.style.boxShadow = "inset 0 0 20px rgba(0, 255, 65, 0.2)";
        setTimeout(() => {
            dash.style.boxShadow = "none";
        }, 100);
    }
}

// Student: Send Feedback
function sendFeedback(category, value) {
    // Visual feedback for the button press
    // (This is handled by the 'active' class toggling mostly, but we can animate here)
    socket.emit('feedback_event', {
        category: category,
        value: value,
        timestamp: Date.now()
    });
}

// Event Listeners for Buttons
document.querySelectorAll('.matrix-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        // Simple toggle effect for feedback
        const btn = e.target;

        // Handling exclusive groups if needed, but for now just flash active
        if (!btn.classList.contains('no-toggle')) {
            btn.classList.add('active');
            setTimeout(() => btn.classList.remove('active'), 200);
        }

        const category = btn.dataset.category;
        const value = btn.dataset.value;

        if (category && value) {
            sendFeedback(category, value);
        }
    });
});
