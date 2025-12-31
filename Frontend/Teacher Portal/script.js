 // Initialize Lucide Icons
        function initIcons() {
            lucide.createIcons();
        }

        // Tab Switching Logic
        function switchTab(tabId) {
            // Update Sidebar UI
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.classList.remove('active');
                item.classList.add('hover:text-slate-300', 'hover:bg-white/5');
            });
            const activeNav = document.getElementById(`nav-${tabId}`);
            if (activeNav) {
                activeNav.classList.add('active');
                activeNav.classList.remove('hover:text-slate-300', 'hover:bg-white/5');
            }

            // Hide all tabs
            document.querySelectorAll('.tab-view').forEach(view => {
                view.classList.add('hidden');
            });

            // Show target tab
            const targetView = document.getElementById(`tab-content-${tabId}`);
            if (targetView) {
                targetView.classList.remove('hidden');
            }

            // Re-render icons for dynamic content
            initIcons();
        }

        // --- SIGN OUT FUNCTIONALITY ---
        function handleSignOut() {
            // Clear any session-related data if needed (mocked here)
            console.log("Signing out user...");
            
            // Visual feedback before redirecting
            const sidebar = document.querySelector('aside');
            if (sidebar) sidebar.style.opacity = '0.5';
            
            // Redirect to the login/landing page
            // Assuming index.html is the main entry point (as per the earlier React-to-HTML conversion)
            window.location.href = '../frontpage/index.html'; 
        }

        // Update current date display
        function updateDate() {
            const dateEl = document.getElementById('current-date');
            if (dateEl) {
                const now = new Date();
                const options = { year: 'numeric', month: 'long', day: 'numeric' };
                dateEl.innerText = now.toLocaleDateString('en-US', options);
            }
        }

        // Initialize App
        window.onload = () => {
            initIcons();
            updateDate();
        };