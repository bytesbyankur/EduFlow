const API_URL = "http://127.0.0.1:8000";
let scanInterval;
let currentClass = "Advanced Neural Networks"; 

window.onload = () => {
    if(window.lucide) lucide.createIcons();
    updateClassContext();
    fetchDashboardData();
};

// --- TAB SWITCHING ---
function switchTab(tabId) {
    document.querySelectorAll('.sidebar-item').forEach(i => {
        i.classList.remove('active', 'bg-white/10', 'text-white');
        i.classList.add('hover:text-slate-300', 'hover:bg-white/5');
    });
    
    const activeBtn = document.getElementById(`nav-${tabId}`);
    if(activeBtn) activeBtn.classList.add('active', 'bg-white/10', 'text-white');
    
    document.querySelectorAll('.tab-view').forEach(v => v.classList.add('hidden'));
    const content = document.getElementById(`tab-content-${tabId}`);
    if(content) content.classList.remove('hidden');
    
    if(window.lucide) lucide.createIcons();
}

// --- DASHBOARD DATA & CLASS CONTEXT ---
async function updateClassContext() {
    const selector = document.getElementById('class-selector');
    currentClass = selector ? selector.value : "Advanced Neural Networks";
    
    // Update Scanner Text (if open)
    const contextLabel = document.getElementById('class-context-display');
    if(contextLabel) contextLabel.innerText = `Class: ${currentClass}`;

    try {
        const res = await fetch(`${API_URL}/get-class-roster?class_name=${encodeURIComponent(currentClass)}`);
        const data = await res.json();
        
        // Update Total Students Count
        const totalStat = document.getElementById('stat-total');
        if(totalStat) totalStat.innerText = data.count;
        
        // Populate Roster Table
        const rosterBody = document.getElementById('roster-table');
        if(rosterBody) {
            rosterBody.innerHTML = "";
            if(data.students.length === 0) {
                 rosterBody.innerHTML = `<tr><td colspan="2" class="px-6 py-4 text-center text-slate-400 text-xs font-bold uppercase">No students enrolled</td></tr>`;
            } else {
                data.students.forEach(student => {
                    const html = `
                        <tr class="hover:bg-slate-50 border-b border-slate-100">
                            <td class="px-6 py-4 font-bold text-slate-700">${student}</td>
                            <td class="px-6 py-4"><span class="bg-slate-100 text-slate-500 px-3 py-1 rounded-lg text-[10px] font-black uppercase">Enrolled</span></td>
                        </tr>`;
                    rosterBody.insertAdjacentHTML('beforeend', html);
                });
            }
        }
        // Refresh Dashboard Logs too
        fetchDashboardData();
    } catch (e) { console.error(e); }
}

async function fetchDashboardData() {
    try {
        const res = await fetch(`${API_URL}/get-dashboard-data`);
        const data = await res.json();
        
        const presentStat = document.getElementById('stat-present');
        if(presentStat) presentStat.innerText = data.stats.present_today;
        
        const tbody = document.getElementById('attendance-table');
        if(tbody) {
            tbody.innerHTML = "";
            data.recent_logs.forEach(row => {
                // row[0] is ID, row[1] is Name, row[2] is Time, row[3] is Class
                const html = `
                    <tr class="hover:bg-slate-50 border-b border-slate-100">
                        <td class="px-6 py-4 text-xs font-bold text-slate-400">${row[0] || 'Unknown'}</td>
                        <td class="px-6 py-4 font-black text-slate-800">${row[1]}</td>
                        <td class="px-6 py-4"><span class="bg-green-100 text-green-600 px-3 py-1 rounded-lg text-[10px] font-black uppercase">Present</span></td>
                        <td class="px-6 py-4 text-xs font-bold text-slate-500">${row[2]}</td>
                    </tr>`;
                tbody.insertAdjacentHTML('beforeend', html);
            });
        }
    } catch (e) { console.error(e); }
}

// --- SCANNER LOGIC ---
function startScanner() {
    document.getElementById('scanner-modal').style.display = 'flex';
    const video = document.getElementById('webcam');
    const status = document.getElementById('scan-status');
    
    const selectedClass = document.getElementById('class-selector').value;
    status.innerText = `🔍 Scanning for ${selectedClass}...`;

    navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
        video.srcObject = stream;
        
        scanInterval = setInterval(() => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            canvas.toBlob(blob => {
                const formData = new FormData();
                formData.append('file', blob, 'scan.jpg');
                // IMPORTANT: Send the class name!
                formData.append('class_name', selectedClass); 
                
                fetch(`${API_URL}/mark-attendance`, { method: 'POST', body: formData })
                .then(r => r.json())
                .then(d => {
                    if(d.status === 'success') {
                        status.innerHTML = `<span class="text-green-400">✅ Verified: ${d.students.join(', ')}</span>`;
                        fetchDashboardData();
                    } else if (d.status === 'failed' && d.message.includes('not in this class')) {
                         status.innerHTML = `<span class="text-red-400">⚠️ Wrong Class</span>`;
                    }
                });
            }, 'image/jpeg');
        }, 3000);
    });
}

function stopScanner() {
    document.getElementById('scanner-modal').style.display = 'none';
    clearInterval(scanInterval);
    const video = document.getElementById('webcam');
    if(video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
}

// --- REGISTRATION LOGIC ---
function openRegistrationModal() {
    document.getElementById('regModal').style.display = "flex";
    const video = document.getElementById('register-video');
    navigator.mediaDevices.getUserMedia({ video: true }).then(s => video.srcObject = s);
}

function closeRegModal() {
    document.getElementById('regModal').style.display = "none";
    const video = document.getElementById('register-video');
    if(video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
}

function registerStudent() {
    const nameInput = document.getElementById('new-student-name');
    const classInput = document.getElementById('new-student-class'); // Dropdown
    const video = document.getElementById('register-video');
    const canvas = document.getElementById('register-canvas');
    const btn = document.getElementById('capture-btn');

    if(!nameInput.value) {
        alert("Please enter a name first!");
        return;
    }

    // UI Feedback
    btn.innerText = "Processing...";
    btn.disabled = true;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('name', nameInput.value);
        formData.append('class_name', classInput.value); // Send Selected Class
        formData.append('file', blob, 'register.jpg');

        fetch(`${API_URL}/register-student`, { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            if(data.status === 'success') {
                alert(`✅ ${data.message}`);
                closeRegModal();
                nameInput.value = "";
                // Refresh data to show new student in roster
                updateClassContext(); 
            } else {
                alert("❌ Error: " + data.message);
            }
        })
        .finally(() => {
            btn.innerText = "Capture & Save";
            btn.disabled = false;
        });
    }, 'image/jpeg');
}