/**
 * Study Time Tracker - Main JavaScript
 * Handles UI interactions, animations, and core functionality
 */

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    initNavbar();
    initDropdowns();
    initAnimations();
    initCharts();
    initTimer();
});

// ==================== NAVBAR ====================
function initNavbar() {
    const navbarToggle = document.getElementById('navbarToggle');
    const navbarMenu = document.getElementById('navbarMenu');
    
    if (navbarToggle && navbarMenu) {
        navbarToggle.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
            
            // Toggle icon
            const icon = navbarToggle.querySelector('i');
            if (navbarMenu.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navbarToggle.contains(e.target) && !navbarMenu.contains(e.target)) {
                navbarMenu.classList.remove('active');
                const icon = navbarToggle.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }
}

// ==================== DROPDOWNS ====================
function initDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu) {
            toggle.addEventListener('click', function(e) {
                e.stopPropagation();
                dropdown.classList.toggle('active');
            });
        }
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown.active').forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    });
}

// ==================== ANIMATIONS ====================
function initAnimations() {
    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
                entry.target.classList.remove('hidden');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements with animate-on-scroll class
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        el.classList.add('hidden');
        observer.observe(el);
    });
    
    // Add staggered animation to card grids
    document.querySelectorAll('.dashboard-grid, .grid').forEach(grid => {
        const cards = grid.querySelectorAll('.card, .stat-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('card-entrance');
        });
    });
}

// ==================== CHARTS ====================
function initCharts() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded');
        return;
    }
    
    // Initialize charts on the page
    const chartCanvases = document.querySelectorAll('canvas.chart');
    chartCanvases.forEach(canvas => {
        const chartType = canvas.dataset.type || 'line';
        const chartData = JSON.parse(canvas.dataset.data || '{}');
        
        if (chartData.labels && chartData.datasets) {
            createChart(canvas, chartType, chartData);
        }
    });
}

function createChart(canvas, type, data) {
    const ctx = canvas.getContext('2d');
    
    // Default chart options
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(31, 41, 55, 0.9)',
                titleFont: {
                    size: 14,
                    weight: 'bold'
                },
                bodyFont: {
                    size: 12
                },
                padding: 12,
                cornerRadius: 8,
                displayColors: true
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    font: {
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        size: 11
                    }
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        size: 11
                    }
                }
            }
        }
    };
    
    // Color schemes
    const colorSchemes = {
        primary: {
            background: 'rgba(99, 102, 241, 0.2)',
            border: '#6366f1'
        },
        success: {
            background: 'rgba(16, 185, 129, 0.2)',
            border: '#10b981'
        },
        warning: {
            background: 'rgba(245, 158, 11, 0.2)',
            border: '#f59e0b'
        },
        error: {
            background: 'rgba(239, 68, 68, 0.2)',
            border: '#ef4444'
        }
    };
    
    // Apply color scheme to datasets
    const scheme = colorSchemes[data.scheme || 'primary'];
    data.datasets.forEach(dataset => {
        if (!dataset.backgroundColor) {
            dataset.backgroundColor = scheme.background;
        }
        if (!dataset.borderColor) {
            dataset.borderColor = scheme.border;
        }
        if (!dataset.borderWidth) {
            dataset.borderWidth = 2;
        }
        if (type === 'line' && !dataset.tension) {
            dataset.tension = 0.4;
        }
        if (type === 'line' && !dataset.fill) {
            dataset.fill = true;
        }
    });
    
    new Chart(ctx, {
        type: type,
        data: data,
        options: {
            ...defaultOptions,
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}

// ==================== TIMER ====================
function initTimer() {
    const timerDisplay = document.querySelector('.timer-display');
    const startBtn = document.querySelector('.timer-btn-start');
    const pauseBtn = document.querySelector('.timer-btn-pause');
    const stopBtn = document.querySelector('.timer-btn-stop');
    
    if (!timerDisplay) return;
    
    let seconds = 0;
    let interval = null;
    let isRunning = false;
    let isPaused = false;
    
    function formatTime(totalSeconds) {
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const secs = totalSeconds % 60;
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    function updateDisplay() {
        timerDisplay.textContent = formatTime(seconds);
    }
    
    function startTimer() {
        if (!isRunning) {
            isRunning = true;
            isPaused = false;
            timerDisplay.classList.add('running');
            timerDisplay.classList.remove('paused');
            
            interval = setInterval(() => {
                seconds++;
                updateDisplay();
            }, 1000);
        }
    }
    
    function pauseTimer() {
        if (isRunning && !isPaused) {
            isPaused = true;
            timerDisplay.classList.remove('running');
            timerDisplay.classList.add('paused');
            clearInterval(interval);
        } else if (isPaused) {
            isPaused = false;
            timerDisplay.classList.remove('paused');
            timerDisplay.classList.add('running');
            
            interval = setInterval(() => {
                seconds++;
                updateDisplay();
            }, 1000);
        }
    }
    
    function stopTimer() {
        isRunning = false;
        isPaused = false;
        clearInterval(interval);
        timerDisplay.classList.remove('running', 'paused');
        seconds = 0;
        updateDisplay();
    }
    
    if (startBtn) {
        startBtn.addEventListener('click', startTimer);
    }
    
    if (pauseBtn) {
        pauseBtn.addEventListener('click', pauseTimer);
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopTimer);
    }
}

// ==================== UTILITY FUNCTIONS ====================
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours === 0) {
        return `${minutes}m`;
    }
    return `${hours}h ${minutes}m`;
}

function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        weekday: 'short'
    };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

function formatTime(dateString) {
    const options = { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true
    };
    return new Date(dateString).toLocaleTimeString('en-US', options);
}

// ==================== COUNTER ANIMATION ====================
function animateCounter(element, target, duration = 1000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// ==================== PROGRESS BARS ====================
function animateProgressBar(bar, percentage) {
    bar.style.width = '0%';
    setTimeout(() => {
        bar.style.width = `${percentage}%`;
    }, 100);
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'info', duration = 3000) {
    const container = document.querySelector('.messages-container') || createMessagesContainer();
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} animate-fadeInDown`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'fadeInRight 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

// ==================== MODAL ====================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// ==================== SUBJECT CHIPS ====================
function initSubjectChips() {
    const chips = document.querySelectorAll('.subject-chip');
    
    chips.forEach(chip => {
        chip.addEventListener('click', function() {
            chips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// ==================== SEARCH FUNCTIONALITY ====================
function initSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchResults = document.querySelector('.search-results');
    
    if (searchInput && searchResults) {
        let debounceTimer;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const query = this.value.toLowerCase();
                // Implement search logic here
                console.log('Searching for:', query);
            }, 300);
        });
    }
}

// ==================== EXPORT FUNCTIONS ====================
window.StudyTracker = {
    showToast,
    openModal,
    closeModal,
    formatDuration,
    formatDate,
    formatTime,
    animateCounter,
    animateProgressBar,
    createChart
};