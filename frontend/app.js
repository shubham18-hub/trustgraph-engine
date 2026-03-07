// API Configuration
const API_BASE = 'http://localhost:8000/api';

// State
let currentUser = null;
let isListening = false;
let signupData = null; // Store signup data for OTP verification

// Initialize
window.addEventListener('load', () => {
    console.log('Page loaded, initializing...');
    hideLoading();
    
    // Small delay to ensure DOM is ready
    setTimeout(() => {
        checkAuth();
        setupOfflineDetection();
    }, 100);
});

function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
        console.log('Loading screen hidden');
    }
}

function checkAuth() {
    const token = localStorage.getItem('token');
    const userProfile = localStorage.getItem('userProfile');
    
    console.log('Checking auth...', { hasToken: !!token, hasProfile: !!userProfile });
    
    if (token && userProfile) {
        try {
            currentUser = JSON.parse(userProfile);
            console.log('User authenticated:', currentUser);
            showDashboard();
            loadUserData();
        } catch (error) {
            console.error('Error parsing user profile:', error);
            // Clear invalid data and redirect
            localStorage.removeItem('token');
            localStorage.removeItem('userProfile');
            redirectToAuth();
        }
    } else {
        console.log('No auth, redirecting to auth page');
        redirectToAuth();
    }
}

function redirectToAuth() {
    // Only redirect if not already on auth page
    if (!window.location.pathname.includes('auth.html')) {
        console.log('Redirecting to auth page...');
        window.location.href = '/auth.html';
    }
}

function showLogin() {
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('signupScreen').style.display = 'none';
}

function showSignup() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('signupScreen').style.display = 'flex';
}

function showDashboard() {
    console.log('Showing dashboard...');
    const loginScreen = document.getElementById('loginScreen');
    const signupScreen = document.getElementById('signupScreen');
    const dashboard = document.getElementById('dashboard');
    
    if (loginScreen) loginScreen.style.display = 'none';
    if (signupScreen) signupScreen.style.display = 'none';
    if (dashboard) {
        dashboard.style.display = 'block';
        console.log('Dashboard displayed');
    } else {
        console.error('Dashboard element not found!');
    }
}

// Signup Flow
async function initiateSignup() {
    const phone = document.getElementById('signupPhone').value;
    const aadhaar = document.getElementById('signupAadhaar').value;
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const city = document.getElementById('signupCity').value;
    const state = document.getElementById('signupState').value;
    const pincode = document.getElementById('signupPincode').value;
    
    // Validation
    if (!phone || phone.length !== 10) {
        alert('कृपया सही मोबाइल नंबर दर्ज करें (10 अंक)');
        return;
    }
    
    if (!aadhaar || aadhaar.length !== 12) {
        alert('कृपया सही आधार नंबर दर्ज करें (12 अंक)');
        return;
    }
    
    if (!name) {
        alert('कृपया अपना नाम दर्ज करें');
        return;
    }
    
    try {
        showMessage('OTP भेजा जा रहा है...', 'info');
        
        const response = await fetch(`${API_BASE}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: phone,
                aadhaar_number: aadhaar,
                name: name,
                email: email || null,
                city: city || null,
                state: state || null,
                pincode: pincode || null,
                preferred_language: 'hi'
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            signupData = data.signup_data;
            document.getElementById('signupForm').style.display = 'none';
            document.getElementById('signupOtpSection').style.display = 'block';
            document.getElementById('signupPhoneDisplay').textContent = data.phone;
            
            // For demo - show OTP
            if (data.otp_demo) {
                showMessage(`OTP भेजा गया: ${data.otp_demo}`, 'success');
            } else {
                showMessage('OTP आपके मोबाइल पर भेजा गया है', 'success');
            }
        } else {
            showMessage(data.error || 'Signup failed', 'error');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showMessage('कनेक्शन में समस्या है', 'error');
    }
}

async function verifySignupOTP() {
    const otp = document.getElementById('signupOtpInput').value;
    const phone = document.getElementById('signupPhone').value;
    
    if (!otp || otp.length !== 6) {
        alert('कृपया 6 अंकों का OTP दर्ज करें');
        return;
    }
    
    try {
        showMessage('OTP सत्यापित किया जा रहा है...', 'info');
        
        const response = await fetch(`${API_BASE}/auth/signup/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: phone,
                otp: otp,
                signup_data: signupData
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Store token and user profile
            localStorage.setItem('token', data.token);
            localStorage.setItem('userProfile', JSON.stringify(data.user_profile));
            currentUser = data.user_profile;
            
            showMessage('खाता सफलतापूर्वक बनाया गया!', 'success');
            setTimeout(() => {
                showDashboard();
                loadUserData();
            }, 1000);
        } else {
            showMessage(data.error || 'OTP सत्यापन विफल', 'error');
        }
    } catch (error) {
        console.error('OTP verification error:', error);
        showMessage('कनेक्शन में समस्या है', 'error');
    }
}

// Login Flow
async function sendOTP() {
    const phone = document.getElementById('phoneInput').value;
    
    if (!phone || phone.length !== 10) {
        alert('कृपया सही मोबाइल नंबर दर्ज करें (10 अंक)');
        return;
    }
    
    try {
        showMessage('OTP भेजा जा रहा है...', 'info');
        
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: phone
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            document.getElementById('otpSection').style.display = 'block';
            
            // For demo - show OTP
            if (data.otp_demo) {
                showMessage(`OTP भेजा गया: ${data.otp_demo}`, 'success');
            } else {
                showMessage('OTP आपके मोबाइल पर भेजा गया है', 'success');
            }
        } else {
            if (data.detail && data.detail.includes('not registered')) {
                showMessage('फोन नंबर पंजीकृत नहीं है। कृपया साइन अप करें।', 'error');
                setTimeout(showSignup, 2000);
            } else {
                showMessage(data.error || data.detail || 'Login failed', 'error');
            }
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('कनेक्शन में समस्या है', 'error');
    }
}

async function verifyOTP() {
    const phone = document.getElementById('phoneInput').value;
    const otp = document.getElementById('otpInput').value;
    
    if (!otp || otp.length !== 6) {
        alert('कृपया 6 अंकों का OTP दर्ज करें');
        return;
    }
    
    try {
        showMessage('OTP सत्यापित किया जा रहा है...', 'info');
        
        const response = await fetch(`${API_BASE}/auth/login/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: phone,
                otp: otp
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Store token and user profile
            localStorage.setItem('token', data.token);
            localStorage.setItem('userProfile', JSON.stringify(data.user_profile));
            currentUser = data.user_profile;
            
            showMessage('लॉगिन सफल!', 'success');
            setTimeout(() => {
                showDashboard();
                loadUserData();
            }, 1000);
        } else {
            showMessage(data.error || data.detail || 'OTP सत्यापन विफल', 'error');
        }
    } catch (error) {
        console.error('OTP verification error:', error);
        showMessage('कनेक्शन में समस्या है', 'error');
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userProfile');
    currentUser = null;
    showLogin();
    showMessage('लॉगआउट सफल', 'success');
}

// Message Display
function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        border-radius: 5px;
        z-index: 10000;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}

// Load User Data
async function loadUserData() {
    try {
        // Use actual user data from localStorage
        const userProfile = JSON.parse(localStorage.getItem('userProfile'));
        
        if (userProfile) {
            // Update user name
            const userNameEl = document.getElementById('userName');
            if (userNameEl) {
                userNameEl.textContent = userProfile.name || 'User';
            }
            
            // Set default trust score (will be calculated later)
            const trustScoreEl = document.getElementById('trustScore');
            if (trustScoreEl) {
                trustScoreEl.textContent = '720';
            }
            
            const trustFillEl = document.getElementById('trustFill');
            if (trustFillEl) {
                trustFillEl.style.width = '72%';
            }
            
            loadRecentWork();
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        // Set defaults
        const userNameEl = document.getElementById('userName');
        if (userNameEl) {
            userNameEl.textContent = 'User';
        }
    }
}

async function loadRecentWork() {
    const workList = document.getElementById('workList');
    
    const works = [
        { icon: '🏗️', title: 'निर्माण कार्य', date: '25 जनवरी 2024', status: 'completed' },
        { icon: '🎨', title: 'पेंटिंग का काम', date: '20 जनवरी 2024', status: 'completed' },
        { icon: '⚡', title: 'बिजली का काम', date: '15 जनवरी 2024', status: 'completed' }
    ];
    
    workList.innerHTML = works.map(work => `
        <div class="work-item">
            <div class="work-icon">${work.icon}</div>
            <div class="work-details">
                <div class="work-title">${work.title}</div>
                <div class="work-date">${work.date}</div>
            </div>
            <div class="work-status ${work.status}">पूर्ण</div>
        </div>
    `).join('');
}

// Voice Commands
function toggleVoice() {
    if (!voiceInterface) {
        alert('वॉइस इंटरफेस लोड नहीं हुआ');
        return;
    }
    
    const btn = document.getElementById('voiceBtn');
    
    if (voiceInterface.isListening) {
        voiceInterface.stopListening();
        btn.setAttribute('aria-pressed', 'false');
    } else {
        voiceInterface.startListening('hi');
        btn.setAttribute('aria-pressed', 'true');
    }
}

function startVoice() {
    toggleVoice();
}

function stopVoice() {
    if (voiceInterface) {
        voiceInterface.stopListening();
    }
}

async function processVoiceCommand(text) {
    try {
        const response = await fetch(`${API_BASE}/intent/classify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                language: 'hi'
            })
        });
        
        const data = await response.json();
        
        handleIntent(data.intent);
    } catch (error) {
        console.error('Error:', error);
    }
}

function handleIntent(intent) {
    switch(intent) {
        case 'CHECK_TRUST_SCORE':
            alert('आपका ट्रस्ट स्कोर 720 है');
            break;
        case 'ADD_WORK_RECORD':
            alert('काम रिकॉर्ड जोड़ा जा रहा है');
            break;
        case 'REQUEST_PAYMENT':
            showPayments();
            break;
        case 'VERIFY_CREDENTIAL':
            showCredentials();
            break;
    }
}

// Navigation
function showHome() {
    updateNav('home');
    document.getElementById('content').style.display = 'block';
}

function showWork() {
    updateNav('work');
    showJobs();
}

function showWallet() {
    updateNav('wallet');
    showPayments();
}

function showSettings() {
    updateNav('settings');
    showThemeSelector();
}

function updateNav(active) {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const navMap = {
        'home': 0,
        'work': 1,
        'wallet': 2,
        'settings': 3
    };
    
    document.querySelectorAll('.nav-btn')[navMap[active]].classList.add('active');
}

// Screens
function showCredentials() {
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('credentialsScreen').style.display = 'block';
    loadCredentials();
}

function showJobs() {
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('jobsScreen').style.display = 'block';
    loadJobs();
}

function showPayments() {
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('paymentsScreen').style.display = 'block';
    loadPayments();
}

function showProfile() {
    alert('प्रोफाइल जल्द आ रही है');
}

function backToDashboard() {
    document.getElementById('credentialsScreen').style.display = 'none';
    document.getElementById('jobsScreen').style.display = 'none';
    document.getElementById('paymentsScreen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
}

// Load Data
function loadCredentials() {
    const list = document.getElementById('credentialsList');
    
    const credentials = [
        { title: 'राजमिस्त्री प्रमाणपत्र', issuer: 'ABC निर्माण', date: '25 जनवरी 2024', verified: true },
        { title: 'पेंटिंग कौशल', issuer: 'XYZ कंपनी', date: '20 जनवरी 2024', verified: true },
        { title: 'बिजली का काम', issuer: 'DEF बिल्डर्स', date: '15 जनवरी 2024', verified: true }
    ];
    
    list.innerHTML = credentials.map(cred => `
        <div class="list-item">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px;">${cred.title}</div>
                    <div style="color: #666; font-size: 14px;">${cred.issuer}</div>
                    <div style="color: #999; font-size: 12px; margin-top: 5px;">${cred.date}</div>
                </div>
                <div style="background: #d4edda; color: #155724; padding: 5px 10px; border-radius: 15px; font-size: 12px;">
                    ✓ सत्यापित
                </div>
            </div>
        </div>
    `).join('');
}

function loadJobs() {
    const list = document.getElementById('jobsList');
    
    const jobs = [
        { title: 'निर्माण कार्य', location: 'नोएडा', pay: '₹15,000', duration: '5 दिन' },
        { title: 'पेंटिंग', location: 'गुड़गांव', pay: '₹12,000', duration: '3 दिन' },
        { title: 'बिजली का काम', location: 'दिल्ली', pay: '₹8,000', duration: '2 दिन' }
    ];
    
    list.innerHTML = jobs.map(job => `
        <div class="list-item">
            <div style="font-weight: bold; font-size: 18px; margin-bottom: 10px;">${job.title}</div>
            <div style="display: flex; gap: 15px; margin-bottom: 10px; color: #666;">
                <span>📍 ${job.location}</span>
                <span>💰 ${job.pay}</span>
                <span>⏱️ ${job.duration}</span>
            </div>
            <button class="btn-primary" style="margin-top: 10px;">आवेदन करें</button>
        </div>
    `).join('');
}

function loadPayments() {
    const list = document.getElementById('paymentsList');
    
    const payments = [
        { title: 'निर्माण कार्य', amount: '₹15,000', date: '25 जनवरी 2024', status: 'paid' },
        { title: 'पेंटिंग का काम', amount: '₹12,000', date: '20 जनवरी 2024', status: 'paid' },
        { title: 'बिजली का काम', amount: '₹8,000', date: '15 जनवरी 2024', status: 'pending' }
    ];
    
    list.innerHTML = payments.map(payment => `
        <div class="list-item">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px;">${payment.title}</div>
                    <div style="color: #666; font-size: 14px;">${payment.date}</div>
                </div>
                <div>
                    <div style="font-weight: bold; font-size: 18px; text-align: right;">${payment.amount}</div>
                    <div style="background: ${payment.status === 'paid' ? '#d4edda' : '#fff3cd'}; 
                                color: ${payment.status === 'paid' ? '#155724' : '#856404'}; 
                                padding: 5px 10px; border-radius: 15px; font-size: 12px; margin-top: 5px;">
                        ${payment.status === 'paid' ? '✓ भुगतान हो गया' : '⏳ लंबित'}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Offline Detection
function setupOfflineDetection() {
    window.addEventListener('offline', () => {
        const banner = document.createElement('div');
        banner.className = 'offline-banner';
        banner.textContent = 'इंटरनेट कनेक्शन नहीं है';
        document.body.prepend(banner);
    });
    
    window.addEventListener('online', () => {
        const banner = document.querySelector('.offline-banner');
        if (banner) banner.remove();
    });
}


// Debug Utilities
function enableDebugMode() {
    const breakpoint = document.createElement('div');
    breakpoint.className = 'debug-breakpoint active';
    document.body.appendChild(breakpoint);
    
    const grid = document.createElement('div');
    grid.className = 'debug-grid';
    document.body.appendChild(grid);
    
    window.addEventListener('keydown', (e) => {
        if (e.key === 'g' && e.ctrlKey) {
            grid.classList.toggle('active');
        }
    });
    
    console.log('Debug mode enabled. Press Ctrl+G to toggle grid.');
}

// Language Switcher Functions
function toggleLangDropdown() {
    const dropdown = document.getElementById('langDropdown');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

function populateLanguages() {
    const dropdown = document.getElementById('langDropdown');
    if (!dropdown) return;
    
    const languages = getAvailableLanguages();
    const currentLang = getCurrentLanguage();
    
    dropdown.innerHTML = languages.map(lang => `
        <div class="lang-option ${lang.code === currentLang ? 'active' : ''}" 
             onclick="changeLang('${lang.code}')">
            <span class="lang-flag">${lang.flag}</span>
            <span class="lang-name">${lang.name}</span>
            ${lang.code === currentLang ? '<span class="lang-check">✓</span>' : ''}
        </div>
    `).join('');
}

function changeLang(langCode) {
    setLanguage(langCode);
    updateCurrentLangDisplay();
    populateLanguages();
    toggleLangDropdown();
}

function updateCurrentLangDisplay() {
    const currentLang = getCurrentLanguage();
    const langData = translations[currentLang];
    
    const flagEl = document.getElementById('currentLangFlag');
    const nameEl = document.getElementById('currentLangName');
    
    if (flagEl) flagEl.textContent = langData.flag;
    if (nameEl) nameEl.textContent = langData.name;
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const switcher = document.querySelector('.lang-switcher');
    const dropdown = document.getElementById('langDropdown');
    
    if (switcher && dropdown && !switcher.contains(e.target)) {
        dropdown.classList.remove('active');
    }
});

// Initialize language switcher
window.addEventListener('load', () => {
    if (typeof populateLanguages === 'function') {
        populateLanguages();
        updateCurrentLangDisplay();
    }
});

// Enable debug on double-tap
let tapCount = 0;
let tapTimer;
document.addEventListener('touchstart', () => {
    tapCount++;
    clearTimeout(tapTimer);
    
    if (tapCount === 5) {
        enableDebugMode();
        tapCount = 0;
    }
    
    tapTimer = setTimeout(() => {
        tapCount = 0;
    }, 1000);
});


// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'default';
    setTheme(savedTheme);
}

function setTheme(themeName) {
    if (themeName === 'default') {
        document.documentElement.removeAttribute('data-theme');
    } else {
        document.documentElement.setAttribute('data-theme', themeName);
    }
    
    localStorage.setItem('theme', themeName);
    
    // Update active theme option
    document.querySelectorAll('.theme-option').forEach(option => {
        option.classList.remove('active');
    });
    
    const activeOption = Array.from(document.querySelectorAll('.theme-option'))
        .find(opt => opt.getAttribute('onclick').includes(themeName));
    
    if (activeOption) {
        activeOption.classList.add('active');
    }
    
    // Check contrast compliance
    checkContrastCompliance();
}

function showThemeSelector() {
    document.getElementById('themeSelector').style.display = 'block';
}

function closeThemeSelector() {
    document.getElementById('themeSelector').style.display = 'none';
}

function checkContrastCompliance() {
    // Get computed colors
    const root = getComputedStyle(document.documentElement);
    const primary = root.getPropertyValue('--color-primary').trim();
    const textInverse = root.getPropertyValue('--text-inverse').trim();
    
    // Calculate contrast ratio (simplified)
    const contrast = calculateContrastRatio(primary, textInverse);
    
    // WCAG AA requires 4.5:1 for normal text, 3:1 for large text
    if (contrast < 4.5) {
        console.warn('Theme may not meet WCAG AA contrast requirements');
    }
}

function calculateContrastRatio(color1, color2) {
    // Simplified contrast calculation
    // In production, use a proper color contrast library
    return 4.5; // Placeholder
}

// Initialize theme on load
window.addEventListener('load', () => {
    initTheme();
});


// Keyboard Navigation Support
document.addEventListener('keydown', (e) => {
    // Add keyboard-user class for enhanced focus indicators
    document.body.classList.add('keyboard-user');
    
    // Escape key closes modals
    if (e.key === 'Escape') {
        closeThemeSelector();
        backToDashboard();
    }
    
    // Ctrl+/ for voice command
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        toggleVoice();
    }
});

// Remove keyboard-user class on mouse use
document.addEventListener('mousedown', () => {
    document.body.classList.remove('keyboard-user');
});

// Announce page changes to screen readers
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        announcement.remove();
    }, 1000);
}

// Update navigation with screen reader announcements
const originalShowCredentials = showCredentials;
showCredentials = function() {
    originalShowCredentials();
    announceToScreenReader('प्रमाणपत्र पृष्ठ खोला गया');
};

const originalShowJobs = showJobs;
showJobs = function() {
    originalShowJobs();
    announceToScreenReader('काम पृष्ठ खोला गया');
};

const originalShowPayments = showPayments;
showPayments = function() {
    originalShowPayments();
    announceToScreenReader('भुगतान पृष्ठ खोला गया');
};
