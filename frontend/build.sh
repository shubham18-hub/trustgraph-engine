#!/bin/bash
# Frontend Build and Optimization Script

set -e

echo "Building TrustGraph Frontend..."

# Create dist directory
mkdir -p dist

# Minify CSS
echo "Minifying CSS..."
cat styles.css themes.css accessibility.css | \
  sed 's/\/\*.*\*\///g' | \
  tr -d '\n' | \
  sed 's/  */ /g' > dist/bundle.min.css

# Minify JavaScript
echo "Minifying JavaScript..."
cat app.js voice.js | \
  sed 's/\/\/.*//g' | \
  sed 's/\/\*.*\*\///g' | \
  tr -d '\n' | \
  sed 's/  */ /g' > dist/bundle.min.js

# Update HTML to use minified files
echo "Updating HTML..."
sed 's/styles.css/bundle.min.css/g' index.html | \
  sed 's/themes.css//g' | \
  sed 's/accessibility.css//g' | \
  sed 's/app.js/bundle.min.js/g' | \
  sed 's/voice.js//g' > dist/index.html

# Copy config
cp theme-config.json dist/

# Optimize images (if any)
if [ -d "images" ]; then
  echo "Copying images..."
  cp -r images dist/
fi

# Generate service worker for offline support
echo "Generating service worker..."
cat > dist/sw.js << 'EOF'
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
EOF

# Calculate file sizes
echo ""
echo "Build complete!"
echo "File sizes:"
du -h dist/*

echo ""
echo "Ready for deployment to S3"
