const API_URL = "http://127.0.0.1:8000";
const LOGGED_IN_STUDENT = localStorage.getItem('currentUser'); 

window.onload = () => {
    if (!LOGGED_IN_STUDENT) {
        alert("Please login first!");
        window.location.href = '../frontpage/index.html';
        return;
    }
    if(window.lucide) lucide.createIcons();
    fetchStudentData();
    fetchHistory();
};

// --- TAB SWITCHING LOGIC ---
function switchTab(tabName) {
    // 1. Hide all views
    document.getElementById('view-overview').classList.add('hidden');
    document.getElementById('view-attendance').classList.add('hidden');
    
    // 2. Show selected view
    const targetView = document.getElementById(`view-${tabName}`);
    if (targetView) targetView.classList.remove('hidden');

    // 3. Update Sidebar Buttons
    document.querySelectorAll('.sidebar-btn').forEach(btn => {
        // Reset to inactive style
        btn.className = "sidebar-btn flex items-center w-full p-4 rounded-2xl hover:bg-white/5 transition-all font-black text-xs uppercase tracking-[0.2em] text-slate-400 hover:text-white group";
    });

    // Set active style for clicked button
    const activeBtn = document.getElementById(`btn-${tabName}`);
    if(activeBtn) {
        activeBtn.className = "sidebar-btn flex items-center w-full p-4 rounded-2xl bg-[#7c3aed] text-white font-black text-xs uppercase tracking-[0.2em] shadow-lg shadow-purple-900/20 transition-all hover:scale-[1.02]";
    }
    
    // 4. Refresh Icons
    if(window.lucide) lucide.createIcons();
}

// --- DATA FETCHING ---
// --- 1. DATA FETCHING FUNCTION ---
async function fetchStudentData() {
    try {
        const response = await fetch(`${API_URL}/student/stats/${encodeURIComponent(LOGGED_IN_STUDENT)}`);
        
        if (!response.ok) throw new Error("Student not found");
        
        const data = await response.json();

        // 1. Basic Info (Header & Stats)
        document.getElementById('student-name').innerText = data.name.split(" ")[0];
        document.getElementById('overall-attendance').innerText = `${data.attendance_rate}%`;
        document.getElementById('student-gpa').innerText = data.gpa;
        document.getElementById('student-credits').innerText = data.credits;
        document.getElementById('student-rank').innerText = data.rank;

        // 2. Pass Real Data to Widgets
        updateAttendanceCalculator(data.present_days, data.total_days);
        
        // **CRITICAL UPDATE:** Pass the real graph data array [0, 1, 3...] here
        drawGraph(data.graph_data); 

        // 3. Populate Course List (Detailed Class Stats)
        const courseList = document.getElementById('course-list');
        courseList.innerHTML = ""; 
        
        data.courses.forEach((course) => {
            // Determine visual styles based on status
            let statusColor = "text-green-600 bg-green-50";
            let iconColor = "text-[#7c3aed]"; 
            
            if (course.status === "At Risk") {
                statusColor = "text-orange-600 bg-orange-50";
                iconColor = "text-orange-500";
            } else if (course.status === "Critical") {
                statusColor = "text-red-600 bg-red-50";
                iconColor = "text-red-500";
            }

            const html = `
                <div class="flex items-center p-4 rounded-2xl bg-slate-50 border border-slate-100 mb-3 hover:bg-white hover:shadow-md transition-all">
                    <div class="w-12 h-12 rounded-xl bg-white flex items-center justify-center shadow-sm mr-4">
                        <i data-lucide="book" class="w-6 h-6 ${iconColor}"></i>
                    </div>
                    <div class="flex-1">
                        <h4 class="text-sm font-black text-slate-800">${course.name}</h4>
                        <div class="flex items-center mt-1">
                            <span class="text-[10px] font-bold ${statusColor} px-2 py-0.5 rounded-md uppercase tracking-widest mr-2">${course.status}</span>
                            <span class="text-xs text-slate-400 font-bold">${course.present} / 10 Sessions</span>
                        </div>
                    </div>
                    <div class="text-right">
                         <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Attendance</p>
                         <p class="text-xl font-black text-slate-900">${course.rate}%</p>
                    </div>
                </div>`;
            courseList.insertAdjacentHTML('beforeend', html);
        });

        if(window.lucide) lucide.createIcons();

    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

// --- ATTENDANCE CALCULATOR ---
function updateAttendanceCalculator(present, total) {
    const TARGET = Math.ceil(total * 0.75); // 75% of 30 is ~23
    const needed = Math.max(0, TARGET - present);
    
    const card = document.getElementById('attendance-calc-card');
    const status = document.getElementById('calc-status');
    const msg = document.getElementById('calc-message');
    const bar = document.getElementById('calc-progress-bar');

    // Calculate width
    const percentage = Math.min((present / TARGET) * 100, 100);
    bar.style.width = `${percentage}%`;

    if (present >= TARGET) {
        card.classList.remove('bg-[#0f172a]');
        card.classList.add('bg-green-600'); 
        status.innerText = "You are Safe! 🎉";
        msg.innerText = `Great job! You have attended ${present} classes. You are above the 75% threshold.`;
    } else {
        card.classList.remove('bg-green-600');
        card.classList.add('bg-[#0f172a]'); 
        status.innerText = `Attend ${needed} More`;
        msg.innerText = `To reach 75% eligibility, you must attend ${needed} more classes out of the remaining sessions.`;
    }
}

// --- 2. GRAPH GENERATOR FUNCTION ---
function drawGraph(dataPoints) {
    const svg = document.getElementById('attendance-graph');
    
    // Safety check: Stop if SVG is missing or no data
    if(!svg || !dataPoints || dataPoints.length === 0) return;

    // 1. Determine Scale (Height)
    // Find the highest number in the week. Set min height to 3 to prevent flatlines.
    const maxVal = Math.max(...dataPoints, 3); 
    
    // 2. Generate Coordinate String
    const coordinates = dataPoints.map((val, index) => {
        // X Axis: Spread points evenly (0 to 100)
        const x = (index / (dataPoints.length - 1)) * 100;
        
        // Y Axis: Scale value to fit 40px height within 50px SVG (leaves 10px padding)
        const y = 50 - ((val / maxVal) * 40); 
        return `${x},${y}`;
    }).join(" ");

    // 3. Clear previous graph
    svg.innerHTML = "";

    // 4. Draw the Line
    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    polyline.setAttribute("points", coordinates);
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", "#7c3aed"); // Purple
    polyline.setAttribute("stroke-width", "3");
    polyline.setAttribute("stroke-linecap", "round");
    polyline.setAttribute("stroke-linejoin", "round");
    // Add glow effect
    polyline.style.filter = "drop-shadow(0px 4px 4px rgba(124, 58, 237, 0.3))";
    
    svg.appendChild(polyline);
    
    // 5. Draw Dots at Data Points
    dataPoints.forEach((val, index) => {
        const x = (index / (dataPoints.length - 1)) * 100;
        const y = 50 - ((val / maxVal) * 40);
        
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", "2.5"); // Dot size
        circle.setAttribute("fill", "white");
        circle.setAttribute("stroke", "#7c3aed");
        circle.setAttribute("stroke-width", "2");
        
        // Tooltip (hover text)
        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = `${val} Classes`;
        circle.appendChild(title);

        svg.appendChild(circle);
    });
}

// --- NEW: FETCH FULL HISTORY ---
async function fetchHistory() {
    try {
        const response = await fetch(`${API_URL}/student/history/${encodeURIComponent(LOGGED_IN_STUDENT)}`);
        const data = await response.json();
        
        const listContainer = document.getElementById('history-list');
        listContainer.innerHTML = ""; // Clear loader
        
        if (data.history.length === 0) {
            listContainer.innerHTML = `<p class="text-center text-slate-400 text-xs font-bold mt-10">No records found.</p>`;
            return;
        }

        data.history.forEach(log => {
            // Format Date (e.g., "2026-01-08" -> "JAN 08")
            const dateObj = new Date(log.date);
            const month = dateObj.toLocaleString('default', { month: 'short' }).toUpperCase();
            const day = String(dateObj.getDate()).padStart(2, '0');

            const html = `
                <div class="flex items-center p-3 rounded-2xl bg-slate-50 border border-slate-100">
                    <div class="flex-shrink-0 w-12 text-center mr-4">
                        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">${month}</p>
                        <p class="text-xl font-black text-slate-800 leading-none">${day}</p>
                    </div>
                    <div class="flex-1 border-l border-slate-200 pl-4">
                        <h4 class="text-xs font-black text-slate-700">${log.class}</h4>
                        <p class="text-[10px] font-bold text-slate-400 mt-0.5">Checked in at <span class="text-purple-600">${log.time}</span></p>
                    </div>
                    <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
                </div>
            `;
            listContainer.insertAdjacentHTML('beforeend', html);
        });

    } catch (error) {
        console.error("Error loading history:", error);
    }
}