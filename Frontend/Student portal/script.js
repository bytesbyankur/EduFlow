const API_URL = "http://127.0.0.1:8000";

// --- CHANGED: GET REAL USER FROM LOGIN ---
// We now get the name stored by the login page instead of hardcoding it.
const LOGGED_IN_STUDENT = localStorage.getItem('currentUser'); 

// --- INITIALIZATION ---
window.onload = () => {
    // 1. SECURITY CHECK
    // If no one is logged in, kick them back to the login page.
    if (!LOGGED_IN_STUDENT) {
        alert("Please login first!");
        window.location.href = '../frontpage/index.html';
        return;
    }

    if(window.lucide) lucide.createIcons();
    fetchStudentData();
    setupNavigation();
};

// --- 2. FETCH DATA FROM BACKEND ---
// --- REPLACE THE fetchStudentData FUNCTION ---

async function fetchStudentData() {
    try {
        const response = await fetch(`${API_URL}/student/stats/${encodeURIComponent(LOGGED_IN_STUDENT)}`);
        
        if (!response.ok) throw new Error("Student not found");
        
        const data = await response.json();

        // 1. Update Basic Info
        document.getElementById('student-name').innerText = data.name.split(" ")[0];

        // 2. Update The Metrics Grid (NEW)
        document.getElementById('overall-attendance').innerText = `${data.attendance_rate}%`;
        document.getElementById('student-gpa').innerText = data.gpa;
        document.getElementById('student-credits').innerText = data.credits;
        document.getElementById('student-rank').innerText = data.rank;
        
        // ... (Rest of course list logic remains the same) ...

    } catch (error) {
        console.error("Error:", error);
    }
}

// --- 3. NAVIGATION LOGIC ---
function setupNavigation() {
    const navButtons = document.querySelectorAll('nav button');
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Reset all buttons to "Inactive" style
            navButtons.forEach(b => {
                b.className = "flex items-center w-full p-4 rounded-2xl hover:bg-white/5 transition-all font-black text-xs uppercase tracking-[0.2em] group text-slate-400";
                const icon = b.querySelector('i');
                if(icon) icon.classList.add('group-hover:text-white');
            });

            // Set clicked button to "Active" style
            btn.className = "flex items-center w-full p-4 rounded-2xl bg-[#7c3aed] text-white font-black text-xs uppercase tracking-[0.2em] shadow-lg shadow-purple-900/20 transition-all hover:scale-[1.02]";
        });
    });
}