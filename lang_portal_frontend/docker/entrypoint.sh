#!/bin/bash
set -e

# Replace environment variables in the main.js file
echo "Replacing environment variables in JavaScript files..."
find /usr/share/nginx/html -name "*.js" -exec sed -i "s|VITE_API_URL_PLACEHOLDER|${VITE_API_URL}|g" {} \;

# Start nginx
echo "Starting Nginx..."
exec "$@"
