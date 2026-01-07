const API_URL = "http://127.0.0.1:8000";
let scanInterval;
let currentClass = "Advanced Neural Networks"; 

window.onload = () => {
    if(window.lucide) lucide.createIcons();
    updateClassContext();
};

function switchTab(tabId) {
    document.querySelectorAll('.sidebar-item').forEach(i => {
        i.classList.remove('active', 'bg-white/10', 'text-white');
        i.classList.add('hover:text-slate-300', 'hover:bg-white/5');
    });
    document.getElementById(`nav-${tabId}`).classList.add('active', 'bg-white/10', 'text-white');
    document.querySelectorAll('.tab-view').forEach(v => v.classList.add('hidden'));
    document.getElementById(`tab-content-${tabId}`).classList.remove('hidden');
    if(window.lucide) lucide.createIcons();
}

async function updateClassContext() {
    currentClass = document.getElementById('class-selector').value;
    const contextLabel = document.getElementById('class-context-display');
    if(contextLabel) contextLabel.innerText = `Class: ${currentClass}`;

    try {
        const res = await fetch(`${API_URL}/get-class-roster?class_name=${encodeURIComponent(currentClass)}`);
        const data = await res.json();
        
        document.getElementById('stat-total').innerText = data.count;
        
        const rosterBody = document.getElementById('roster-table');
        if(rosterBody) {
            rosterBody.innerHTML = "";
            data.students.forEach(student => {
                const html = `
                    <tr class="hover:bg-slate-50 border-b border-slate-100">
                        <td class="px-6 py-4 font-bold text-slate-700">${student}</td>
                        <td class="px-6 py-4"><span class="bg-slate-100 text-slate-500 px-3 py-1 rounded-lg text-[10px] font-black uppercase">Enrolled</span></td>
                    </tr>`;
                rosterBody.insertAdjacentHTML('beforeend', html);
            });
        }
        fetchDashboardData();
    } catch (e) { console.error(e); }
}

async function fetchDashboardData() {
    const res = await fetch(`${API_URL}/get-dashboard-data`);
    const data = await res.json();
    
    document.getElementById('stat-present').innerText = data.stats.present_today;
    
    const tbody = document.getElementById('attendance-table');
    tbody.innerHTML = "";
    data.recent_logs.forEach(row => {
        const html = `
            <tr class="hover:bg-slate-50 border-b border-slate-100">
                <td class="px-6 py-4 text-xs font-bold text-slate-400">REG-2025-${String(row[0]).padStart(4,'0')}</td>
                <td class="px-6 py-4 font-black text-slate-800">${row[1]}</td>
                <td class="px-6 py-4"><span class="bg-green-100 text-green-600 px-3 py-1 rounded-lg text-[10px] font-black uppercase">Present</span></td>
                <td class="px-6 py-4 text-xs font-bold text-slate-500">${row[2]}</td>
            </tr>`;
        tbody.insertAdjacentHTML('beforeend', html);
    });
}

// --- SCANNER ---
function startScanner() {
    document.getElementById('scanner-modal').style.display = 'flex';
    const video = document.getElementById('webcam');
    const status = document.getElementById('scan-status');
    
    navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
        video.srcObject = stream;
        status.innerText = `🔍 Scanning for ${currentClass}...`;
        
        scanInterval = setInterval(() => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            canvas.toBlob(blob => {
                const formData = new FormData();
                formData.append('file', blob, 'scan.jpg');
                
                fetch(`${API_URL}/mark-attendance`, { method: 'POST', body: formData })
                .then(r => r.json())
                .then(d => {
                    if(d.status === 'success') {
                        status.innerHTML = `<span class="text-green-400">✅ Identified: ${d.students.join(', ')}</span>`;
                        fetchDashboardData();
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

// --- REGISTRATION ---
function openRegistrationModal() {
    document.getElementById('regModal').style.display = "flex";
    const video = document.getElementById('regVideo');
    navigator.mediaDevices.getUserMedia({ video: true }).then(s => video.srcObject = s);
}

function closeRegModal() {
    document.getElementById('regModal').style.display = "none";
    const video = document.getElementById('regVideo');
    if(video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
}

// --- REPLACE THE OLD captureAndRegister FUNCTION WITH THIS ---

function captureAndRegister() {
    const nameInput = document.getElementById('regName');
    const name = nameInput.value.trim();
    
    if(!name) {
        alert("Please enter a student name first!");
        return;
    }
    
    const video = document.getElementById('regVideo');
    // Safety check: Is video playing?
    if (!video.srcObject || video.videoWidth === 0) {
        alert("Camera is not ready. Please wait a moment.");
        return;
    }

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    // Change button text to show it's working
    const saveBtn = document.querySelector("button[onclick='captureAndRegister()']");
    const originalText = saveBtn.innerText;
    saveBtn.innerText = "SAVING...";
    saveBtn.disabled = true;

    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('file', blob, 'register.jpg');
        
        fetch(`${API_URL}/register-student`, { 
            method: 'POST', 
            body: formData 
        })
        .then(async response => {
            const data = await response.json();
            
            // Check if Backend reported an error (like 422 or 500)
            if (!response.ok) {
                // FastAPI usually sends errors in 'detail'
                const errorMsg = data.detail || data.message || "Unknown Server Error";
                throw new Error(errorMsg);
            }
            return data;
        })
        .then(data => {
            // Success!
            alert("✅ " + (data.message || "Student Registered!"));
            closeRegModal();
            nameInput.value = ""; // Clear input
        })
        .catch(err => {
            console.error("Registration Failed:", err);
            alert("❌ Failed: " + err.message);
        })
        .finally(() => {
            // Reset button
            saveBtn.innerText = originalText;
            saveBtn.disabled = false;
        });
    }, 'image/jpeg');
}