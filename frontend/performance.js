// Performance Optimization for Low Bandwidth Networks

// Lazy Loading Images
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Preload Critical Resources
function preloadCritical() {
    const criticalResources = [
        { href: '/bundle.min.css', as: 'style' },
        { href: '/bundle.min.js', as: 'script' }
    ];
    
    criticalResources.forEach(resource => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = resource.href;
        link.as = resource.as;
        document.head.appendChild(link);
    });
}

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('Service Worker registration failed'));
    });
}

// Network Quality Detection
class NetworkMonitor {
    constructor() {
        this.connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        this.quality = 'unknown';
        this.init();
    }
    
    init() {
        if (this.connection) {
            this.updateQuality();
            this.connection.addEventListener('change', () => this.updateQuality());
        }
    }
    
    updateQuality() {
        const effectiveType = this.connection.effectiveType;
        
        switch(effectiveType) {
            case 'slow-2g':
            case '2g':
                this.quality = 'poor';
                this.enableDataSaver();
                break;
            case '3g':
                this.quality = 'moderate';
                this.optimizeFor3G();
                break;
            case '4g':
                this.quality = 'good';
                break;
            default:
                this.quality = 'unknown';
        }
        
        console.log(`Network quality: ${this.quality} (${effectiveType})`);
    }
    
    enableDataSaver() {
        // Disable auto-play
        document.querySelectorAll('video, audio').forEach(media => {
            media.preload = 'none';
        });
        
        // Show data saver notice
        this.showDataSaverNotice();
    }
    
    optimizeFor3G() {
        // Reduce image quality
        document.querySelectorAll('img').forEach(img => {
            if (img.dataset.lowres) {
                img.src = img.dataset.lowres;
            }
        });
    }
    
    showDataSaverNotice() {
        const notice = document.createElement('div');
        notice.className = 'data-saver-notice';
        notice.innerHTML = `
            <span>📶 धीमा नेटवर्क - डेटा सेवर मोड सक्रिय</span>
            <button onclick="this.parentElement.remove()">✕</button>
        `;
        document.body.appendChild(notice);
    }
}

// Request Batching
class RequestBatcher {
    constructor() {
        this.queue = [];
        this.batchSize = 5;
        this.batchDelay = 100;
        this.timer = null;
    }
    
    add(request) {
        this.queue.push(request);
        
        if (this.queue.length >= this.batchSize) {
            this.flush();
        } else {
            this.scheduleBatch();
        }
    }
    
    scheduleBatch() {
        if (this.timer) clearTimeout(this.timer);
        this.timer = setTimeout(() => this.flush(), this.batchDelay);
    }
    
    async flush() {
        if (this.queue.length === 0) return;
        
        const batch = this.queue.splice(0, this.batchSize);
        
        try {
            await fetch('/api/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ requests: batch })
            });
        } catch (error) {
            console.error('Batch request failed:', error);
        }
    }
}

// Cache Management
class CacheManager {
    constructor() {
        this.cacheName = 'trustgraph-cache-v1';
        this.maxAge = 24 * 60 * 60 * 1000; // 24 hours
    }
    
    async get(key) {
        const cached = localStorage.getItem(key);
        if (!cached) return null;
        
        const data = JSON.parse(cached);
        const age = Date.now() - data.timestamp;
        
        if (age > this.maxAge) {
            localStorage.removeItem(key);
            return null;
        }
        
        return data.value;
    }
    
    set(key, value) {
        const data = {
            value: value,
            timestamp: Date.now()
        };
        localStorage.setItem(key, JSON.stringify(data));
    }
    
    clear() {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('trustgraph-')) {
                localStorage.removeItem(key);
            }
        });
    }
}

// Progressive Loading
function progressiveLoad() {
    // Load critical content first
    loadCriticalContent();
    
    // Load secondary content after delay
    setTimeout(() => loadSecondaryContent(), 1000);
    
    // Load tertiary content on interaction
    document.addEventListener('scroll', loadTertiaryContent, { once: true });
}

function loadCriticalContent() {
    // Trust score, voice button
    console.log('Loading critical content');
}

function loadSecondaryContent() {
    // Recent work, quick actions
    console.log('Loading secondary content');
}

function loadTertiaryContent() {
    // Additional features
    console.log('Loading tertiary content');
}

// Performance Monitoring
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
    }
    
    measure(name, fn) {
        const start = performance.now();
        const result = fn();
        const duration = performance.now() - start;
        
        this.metrics[name] = duration;
        
        if (duration > 100) {
            console.warn(`Slow operation: ${name} took ${duration.toFixed(2)}ms`);
        }
        
        return result;
    }
    
    async measureAsync(name, fn) {
        const start = performance.now();
        const result = await fn();
        const duration = performance.now() - start;
        
        this.metrics[name] = duration;
        
        if (duration > 1000) {
            console.warn(`Slow async operation: ${name} took ${duration.toFixed(2)}ms`);
        }
        
        return result;
    }
    
    getMetrics() {
        return this.metrics;
    }
    
    reportToAnalytics() {
        // Send metrics to analytics service
        console.log('Performance metrics:', this.metrics);
    }
}

// Initialize
const networkMonitor = new NetworkMonitor();
const requestBatcher = new RequestBatcher();
const cacheManager = new CacheManager();
const perfMonitor = new PerformanceMonitor();

// Export for use in other modules
window.TrustGraphPerf = {
    networkMonitor,
    requestBatcher,
    cacheManager,
    perfMonitor,
    lazyLoadImages,
    progressiveLoad
};

// Auto-initialize on load
window.addEventListener('load', () => {
    lazyLoadImages();
    progressiveLoad();
});
