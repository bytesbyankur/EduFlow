// Initialize Lucide Icons
        lucide.createIcons();

        // Navigation Tab Switching
        function switchTab(tabId) {
            // Update Sidebar UI
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.classList.remove('active');
                item.classList.add('text-slate-500', 'hover:text-slate-300', 'hover:bg-white/5');
            });
            const activeNav = document.getElementById(`nav-${tabId}`);
            activeNav.classList.add('active');
            activeNav.classList.remove('text-slate-500', 'hover:text-slate-300', 'hover:bg-white/5');

            // Hide all tab content
            document.getElementById('tab-content-overview').classList.add('hidden');
            document.getElementById('tab-content-attendance').classList.add('hidden');
            document.getElementById('tab-content-courses').classList.add('hidden');
            document.getElementById('tab-content-notes').classList.add('hidden');

            // Show active tab content
            document.getElementById(`tab-content-${tabId}`).classList.remove('hidden');
            
            // Re-render icons for dynamic content if necessary
            lucide.createIcons();
        }