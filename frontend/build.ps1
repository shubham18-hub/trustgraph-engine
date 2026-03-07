# Frontend Build and Optimization Script (PowerShell)

Write-Host "Building TrustGraph Frontend..." -ForegroundColor Cyan

# Create dist directory
if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

# Minify CSS
Write-Host "Minifying CSS..." -ForegroundColor Yellow
$css = Get-Content styles.css, themes.css, accessibility.css -Raw
$css = $css -replace '/\*.*?\*/', '' -replace '\s+', ' '
$css | Set-Content dist/bundle.min.css

# Minify JavaScript
Write-Host "Minifying JavaScript..." -ForegroundColor Yellow
$js = Get-Content app.js, voice.js -Raw
$js = $js -replace '//.*', '' -replace '/\*.*?\*/', '' -replace '\s+', ' '
$js | Set-Content dist/bundle.min.js

# Update HTML to use minified files
Write-Host "Updating HTML..." -ForegroundColor Yellow
$html = Get-Content index.html -Raw
$html = $html -replace 'styles.css', 'bundle.min.css'
$html = $html -replace '<link rel="stylesheet" href="themes.css">', ''
$html = $html -replace '<link rel="stylesheet" href="accessibility.css">', ''
$html = $html -replace 'app.js', 'bundle.min.js'
$html = $html -replace '<script src="voice.js"></script>', ''
$html | Set-Content dist/index.html

# Copy config
Copy-Item theme-config.json dist/

# Generate service worker for offline support
Write-Host "Generating service worker..." -ForegroundColor Yellow
@'
const CACHE_NAME = 'trustgraph-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/bundle.min.css',
  '/bundle.min.js',
  '/theme-config.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
'@ | Set-Content dist/sw.js

# Calculate file sizes
Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "File sizes:" -ForegroundColor Cyan
Get-ChildItem dist | ForEach-Object {
    $size = "{0:N2} KB" -f ($_.Length / 1KB)
    Write-Host "  $($_.Name): $size"
}

Write-Host ""
Write-Host "Ready for deployment to S3" -ForegroundColor Green
