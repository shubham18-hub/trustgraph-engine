// Web Speech API Voice Interface with Indian Language Support

class VoiceInterface {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.currentLanguage = 'hi-IN';
        this.debugMode = false;
        
        // Indian language support
        this.languages = {
            'hi': { code: 'hi-IN', name: 'हिन्दी' },
            'en': { code: 'en-IN', name: 'English' },
            'ta': { code: 'ta-IN', name: 'தமிழ்' },
            'te': { code: 'te-IN', name: 'తెలుగు' },
            'bn': { code: 'bn-IN', name: 'বাংলা' },
            'mr': { code: 'mr-IN', name: 'मराठी' },
            'gu': { code: 'gu-IN', name: 'ગુજરાતી' },
            'kn': { code: 'kn-IN', name: 'ಕನ್ನಡ' },
            'ml': { code: 'ml-IN', name: 'മലയാളം' },
            'pa': { code: 'pa-IN', name: 'ਪੰਜਾਬੀ' }
        };
        
        this.init();
    }
    
    init() {
        this.checkBrowserSupport();
        this.checkHTTPS();
        this.setupRecognition();
        this.logDebug('Voice interface initialized');
    }
    
    checkBrowserSupport() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showError('browser-not-supported', 
                'आपका ब्राउज़र वॉइस कमांड सपोर्ट नहीं करता। कृपया Chrome या Edge का उपयोग करें।');
            return false;
        }
        
        if (!this.synthesis) {
            this.showError('synthesis-not-supported', 
                'वॉइस आउटपुट उपलब्ध नहीं है।');
            return false;
        }
        
        this.logDebug('Browser supports Web Speech API');
        return true;
    }
    
    checkHTTPS() {
        if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
            this.showError('https-required', 
                'वॉइस कमांड के लिए HTTPS आवश्यक है। कृपया सुरक्षित कनेक्शन का उपयोग करें।');
            return false;
        }
        this.logDebug('HTTPS check passed');
        return true;
    }
    
    setupRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 3;
        this.recognition.lang = this.currentLanguage;
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.onListeningStart();
            this.logDebug('Recognition started');
        };
        
        this.recognition.onresult = (event) => {
            const results = event.results;
            const transcript = results[results.length - 1][0].transcript;
            const confidence = results[results.length - 1][0].confidence;
            
            this.logDebug(`Transcript: ${transcript}, Confidence: ${confidence}`);
            this.onTranscript(transcript, confidence);
        };
        
        this.recognition.onerror = (event) => {
            this.logDebug(`Recognition error: ${event.error}`);
            this.handleRecognitionError(event.error);
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.onListeningEnd();
            this.logDebug('Recognition ended');
        };
    }
    
    async requestMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            this.logDebug('Microphone permission granted');
            return true;
        } catch (error) {
            this.logDebug(`Microphone permission error: ${error.message}`);
            this.showError('microphone-permission', 
                'माइक्रोफ़ोन की अनुमति आवश्यक है। कृपया ब्राउज़र सेटिंग्स में अनुमति दें।');
            return false;
        }
    }
    
    async startListening(language = 'hi') {
        if (this.isListening) {
            this.stopListening();
            return;
        }
        
        const hasPermission = await this.requestMicrophonePermission();
        if (!hasPermission) {
            return;
        }
        
        this.currentLanguage = this.languages[language]?.code || 'hi-IN';
        this.recognition.lang = this.currentLanguage;
        
        try {
            this.recognition.start();
            this.logDebug(`Started listening in ${this.currentLanguage}`);
        } catch (error) {
            this.logDebug(`Start listening error: ${error.message}`);
            this.showError('recognition-failed', 'वॉइस रिकग्निशन शुरू नहीं हो सका।');
        }
    }
    
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.logDebug('Stopped listening');
        }
    }
    
    speak(text, language = 'hi') {
        if (!this.synthesis) {
            this.logDebug('Speech synthesis not available');
            return;
        }
        
        // Cancel any ongoing speech
        this.synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = this.languages[language]?.code || 'hi-IN';
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Try to find Indian voice
        const voices = this.synthesis.getVoices();
        const indianVoice = voices.find(voice => 
            voice.lang.startsWith(language) || voice.lang.includes('IN')
        );
        
        if (indianVoice) {
            utterance.voice = indianVoice;
            this.logDebug(`Using voice: ${indianVoice.name}`);
        }
        
        utterance.onstart = () => {
            this.logDebug('Speech started');
        };
        
        utterance.onend = () => {
            this.logDebug('Speech ended');
        };
        
        utterance.onerror = (event) => {
            this.logDebug(`Speech error: ${event.error}`);
        };
        
        this.synthesis.speak(utterance);
    }
    
    async processCommand(transcript) {
        try {
            const response = await fetch(`${API_BASE}/intent/classify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: transcript,
                    language: this.currentLanguage.split('-')[0]
                })
            });
            
            if (!response.ok) {
                throw new Error('API request failed');
            }
            
            const data = await response.json();
            this.logDebug(`Intent: ${data.intent}, Confidence: ${data.confidence}`);
            
            return data;
        } catch (error) {
            this.logDebug(`API error: ${error.message}`);
            this.showError('api-connectivity', 
                'सर्वर से कनेक्ट नहीं हो सका। कृपया इंटरनेट कनेक्शन जांचें।');
            return null;
        }
    }
    
    handleRecognitionError(error) {
        const errorMessages = {
            'no-speech': 'कोई आवाज़ नहीं सुनाई दी। कृपया फिर से बोलें।',
            'audio-capture': 'माइक्रोफ़ोन एक्सेस नहीं हो सका।',
            'not-allowed': 'माइक्रोफ़ोन की अनुमति नहीं दी गई।',
            'network': 'नेटवर्क एरर। कृपया इंटरनेट कनेक्शन जांचें।',
            'aborted': 'वॉइस रिकग्निशन बंद हो गया।',
            'bad-grammar': 'वॉइस रिकग्निशन में समस्या।'
        };
        
        const message = errorMessages[error] || 'वॉइस रिकग्निशन में समस्या आई।';
        this.showError(error, message);
    }
    
    showError(type, message) {
        console.error(`[Voice Error] ${type}: ${message}`);
        
        // Show error to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'voice-error';
        errorDiv.innerHTML = `
            <div class="error-icon">⚠️</div>
            <div class="error-message">${message}</div>
            <button onclick="this.parentElement.remove()" class="error-close">✕</button>
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    
    logDebug(message) {
        if (this.debugMode) {
            console.log(`[Voice Debug] ${new Date().toISOString()}: ${message}`);
        }
    }
    
    enableDebug() {
        this.debugMode = true;
        this.logDebug('Debug mode enabled');
    }
    
    // Callbacks (to be overridden)
    onListeningStart() {}
    onListeningEnd() {}
    onTranscript(text, confidence) {}
}

// Global voice interface instance
let voiceInterface = null;

function initVoiceInterface() {
    voiceInterface = new VoiceInterface();
    
    // Override callbacks
    voiceInterface.onListeningStart = () => {
        const btn = document.getElementById('voiceBtn');
        if (btn) {
            btn.classList.add('listening');
        }
        
        const text = document.getElementById('voiceText');
        if (text) {
            text.textContent = 'सुन रहा हूँ...';
            text.setAttribute('aria-live', 'polite');
        }
    };
    
    voiceInterface.onListeningEnd = () => {
        const btn = document.getElementById('voiceBtn');
        if (btn) {
            btn.classList.remove('listening');
        }
    };
    
    voiceInterface.onTranscript = async (text, confidence) => {
        const textDiv = document.getElementById('voiceText');
        if (textDiv) {
            textDiv.textContent = text;
        }
        
        // Process command if confidence is high enough
        if (confidence > 0.7) {
            const result = await voiceInterface.processCommand(text);
            if (result) {
                handleVoiceIntent(result);
            }
        }
    };
}

function handleVoiceIntent(result) {
    const responses = {
        'CHECK_TRUST_SCORE': 'आपका ट्रस्ट स्कोर 720 है। यह एक अच्छा स्कोर है।',
        'ADD_WORK_RECORD': 'आपका काम रिकॉर्ड जोड़ा जा रहा है।',
        'REQUEST_PAYMENT': 'आपका पेमेंट रिक्वेस्ट भेजा जा रहा है।',
        'VERIFY_CREDENTIAL': 'आपके पास 15 वेरिफाइड सर्टिफिकेट हैं।',
        'GET_HELP': 'मैं आपकी मदद के लिए यहाँ हूँ।'
    };
    
    const response = responses[result.intent] || 'मुझे समझ नहीं आया।';
    
    // Speak response
    voiceInterface.speak(response);
    
    // Execute action
    handleIntent(result.intent);
}

// Initialize on page load
window.addEventListener('load', () => {
    initVoiceInterface();
});
