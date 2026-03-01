// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Check Bedrock status on page load
document.addEventListener('DOMContentLoaded', async () => {
    await checkBedrockStatus();
    initializeScrollAnimations();
    initializeNavigation();
});

// Check Bedrock connectivity
async function checkBedrockStatus() {
    const statusElement = document.getElementById('bedrockStatus');
    const statusDot = document.querySelector('.status-dot');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const data = await response.json();
        
        if (data.services.bedrock === 'connected') {
            statusElement.textContent = '✓ Bedrock Connected';
            statusDot.style.background = 'var(--success)';
        } else {
            statusElement.textContent = '⚠ Fallback Mode';
            statusDot.style.background = 'var(--warning)';
        }
    } catch (error) {
        statusElement.textContent = '✗ Server Offline';
        statusDot.style.background = 'var(--error)';
        console.error('Health check failed:', error);
    }
}

// Set command in input
function setCommand(text) {
    document.getElementById('hindiInput').value = text;
    // Scroll to input
    document.getElementById('hindiInput').focus();
}

// Classify intent using Bedrock
async function classifyIntent() {
    const text = document.getElementById('hindiInput').value;
    const language = document.getElementById('languageSelect').value;
    const resultDiv = document.getElementById('demoResult');
    const resultContent = document.getElementById('resultContent');
    const btnDemo = document.querySelector('.btn-demo');
    const btnText = btnDemo.querySelector('.btn-text');
    const btnLoader = btnDemo.querySelector('.btn-loader');
    
    if (!text.trim()) {
        alert('Please enter a command');
        return;
    }
    
    // Show loading state
    btnText.style.display = 'none';
    btnLoader.style.display = 'flex';
    btnDemo.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/intent/classify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text, language })
        });
        
        const data = await response.json();
        
        // Display result
        resultDiv.style.display = 'block';
        resultDiv.classList.add('fade-in');
        
        resultContent.innerHTML = `
            <div class="result-item">
                <div class="result-label">Intent:</div>
                <div class="result-value">
                    <span class="intent-badge">${data.intent}</span>
                </div>
            </div>
            
            <div class="result-item">
                <div class="result-label">Confidence:</div>
                <div class="result-value">${(data.confidence * 100).toFixed(1)}%</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${data.confidence * 100}%"></div>
                </div>
            </div>
            
            <div class="result-item">
                <div class="result-label">Latency:</div>
                <div class="result-value">${data.latency_ms.toFixed(0)}ms</div>
            </div>
            
            <div class="result-item">
                <div class="result-label">Source:</div>
                <div class="result-value">
                    ${data.source === 'bedrock' ? '🤖 AWS Bedrock' : '⚙️ Fallback'}
                </div>
            </div>
            
            ${data.reasoning ? `
                <div class="result-item">
                    <div class="result-label">Reasoning:</div>
                    <div class="result-value">${data.reasoning}</div>
                </div>
            ` : ''}
            
            ${data.needs_clarification ? `
                <div class="result-item">
                    <div class="result-label">⚠️ Note:</div>
                    <div class="result-value">Low confidence - may need clarification</div>
                </div>
            ` : ''}
        `;
        
        // Scroll to result
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        resultDiv.style.display = 'block';
        resultContent.innerHTML = `
            <div class="result-item">
                <div class="result-label">❌ Error:</div>
                <div class="result-value">${error.message}</div>
            </div>
            <div class="result-item">
                <div class="result-value">
                    Make sure the server is running: <code>python app.py</code>
                </div>
            </div>
        `;
        console.error('Classification error:', error);
    } finally {
        // Reset button state
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        btnDemo.disabled = false;
    }
}

// Clear result
function clearResult() {
    const resultDiv = document.getElementById('demoResult');
    resultDiv.style.display = 'none';
}

// Voice input (placeholder - requires Web Speech API)
function startVoiceInput() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.lang = 'hi-IN'; // Hindi
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = () => {
            document.querySelector('.btn-voice').style.background = 'var(--error)';
        };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById('hindiInput').value = transcript;
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            alert('Voice input error: ' + event.error);
        };
        
        recognition.onend = () => {
            document.querySelector('.btn-voice').style.background = 'var(--white)';
        };
        
        recognition.start();
    } else {
        alert('Voice input not supported in this browser. Please use Chrome or Edge.');
    }
}

// Scroll to demo section
function scrollToDemo() {
    document.getElementById('demo').scrollIntoView({ behavior: 'smooth' });
}

// Initialize scroll animations
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);
    
    // Observe all feature cards and impact cards
    document.querySelectorAll('.feature-card, .impact-card, .info-card').forEach(el => {
        observer.observe(el);
    });
}

// Initialize navigation
function initializeNavigation() {
    // Smooth scroll for nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            if (targetId.startsWith('#')) {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }
            }
            
            // Update active state
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
    
    // Navbar scroll effect
    let lastScroll = 0;
    window.addEventListener('scroll', () => {
        const navbar = document.querySelector('.navbar');
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.style.boxShadow = 'var(--shadow-md)';
        } else {
            navbar.style.boxShadow = 'none';
        }
        
        lastScroll = currentScroll;
    });
    
    // Mobile menu toggle
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.style.display = navLinks.style.display === 'flex' ? 'none' : 'flex';
        });
    }
}

// Handle Enter key in input
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('hindiInput');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                classifyIntent();
            }
        });
    }
});

// Auto-refresh Bedrock status every 30 seconds
setInterval(checkBedrockStatus, 30000);

// Add some console art
console.log(`
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🇮🇳 TrustGraph Engine - Digital ShramSetu               ║
║                                                           ║
║   Empowering 490 Million Informal Workers                ║
║   Powered by AWS Bedrock GenAI                           ║
║                                                           ║
║   Built with ❤️ for India's informal workforce           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

API Endpoint: ${API_BASE_URL}
Status: Checking...

Try these commands:
• मेरा ट्रस्ट स्कोर क्या है? (What is my trust score?)
• काम पूरा हो गया (Work completed)
• मुझे पैसे चाहिए (I need payment)
`);
