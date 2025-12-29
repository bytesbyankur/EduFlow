// State Management
        let currentRole = 'teacher';

        // Initialize Icons
        function initIcons() {
            lucide.createIcons();
        }

        // Welcome Animation
        function animateTitle() {
            const titleEl = document.getElementById('animated-title');
            const titleText = "EduFlow";
            titleEl.innerHTML = '';
            titleText.split("").forEach((char, i) => {
                const span = document.createElement('span');
                span.innerText = char;
                span.className = 'letter bg-clip-text text-transparent bg-gradient-to-b from-white via-purple-100 to-lavender-400';
                span.style.animationDelay = `${i * 0.1}s`;
                titleEl.appendChild(span);
            });
        }

        // Parallax Mouse Effect
        document.addEventListener('mousemove', (e) => {
            const container = document.getElementById('parallax-container');
            if (!container) return;
            const x = (e.clientX / window.innerWidth) * 20;
            const y = (e.clientY / window.innerHeight) * 20;
            container.style.transform = `translate(${x}px, ${y}px)`;
        });

        // Navigation
        function navigateTo(pageId) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            const targetPage = document.getElementById(pageId + '-page') || document.getElementById(pageId);
            if (targetPage) targetPage.classList.add('active');
            
            if (pageId === 'welcome') {
                animateTitle();
            }
            initIcons();
        }

        // Role Selection
        function setRole(role) {
            currentRole = role;
            const btnTeacher = document.getElementById('toggle-teacher');
            const btnStudent = document.getElementById('toggle-student');
            const label = document.getElementById('user-label');
            const input = document.getElementById('user-input');
            const loginBtn = document.getElementById('login-btn');
            const forgotLink = document.getElementById('forgot-link');

            if (role === 'teacher') {
                btnTeacher.className = 'flex-1 py-3 text-xs font-black tracking-widest uppercase rounded-xl transition-all bg-white text-indigo-700 shadow-md';
                btnStudent.className = 'flex-1 py-3 text-xs font-black tracking-widest uppercase rounded-xl transition-all text-slate-400';
                label.innerText = 'University ID / Email';
                input.placeholder = 'e.g. faculty.miller@edu.com';
                input.className = 'w-full pl-12 pr-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-medium focus:ring-4 focus:bg-white outline-none transition-all focus:ring-indigo-100 focus:border-indigo-600';
                loginBtn.className = 'w-full py-5 rounded-[20px] text-sm font-black text-white tracking-[0.2em] uppercase transition-all shadow-xl active:scale-[0.98] bg-gradient-to-r from-indigo-700 to-blue-800 hover:shadow-indigo-200';
                forgotLink.className = 'font-black tracking-tight hover:underline text-indigo-600';
                document.getElementById('user-icon').setAttribute('data-lucide', 'mail');
            } else {
                btnStudent.className = 'flex-1 py-3 text-xs font-black tracking-widest uppercase rounded-xl transition-all bg-white text-purple-600 shadow-md';
                btnTeacher.className = 'flex-1 py-3 text-xs font-black tracking-widest uppercase rounded-xl transition-all text-slate-400';
                label.innerText = 'Student Reg. Number';
                input.placeholder = 'e.g. REG-2025-0982';
                input.className = 'w-full pl-12 pr-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-medium focus:ring-4 focus:bg-white outline-none transition-all focus:ring-purple-100 focus:border-purple-600';
                loginBtn.className = 'w-full py-5 rounded-[20px] text-sm font-black text-white tracking-[0.2em] uppercase transition-all shadow-xl active:scale-[0.98] bg-gradient-to-r from-purple-600 to-indigo-600 hover:shadow-purple-200';
                forgotLink.className = 'font-black tracking-tight hover:underline text-purple-600';
                document.getElementById('user-icon').setAttribute('data-lucide', 'user');
            }
            initIcons();
        }

        // Auth Logic
        function handleAuth(e) {
            e.preventDefault();
            const loader = document.getElementById('loading-screen');
            loader.style.display = 'flex';
            
            setTimeout(() => {
                loader.style.display = 'none';
                navigateTo(currentRole === 'teacher' ? 'teacher-dash' : 'student-dash');
            }, 1500);
        }

        // Init
        window.onload = () => {
            animateTitle();
            initIcons();
        };