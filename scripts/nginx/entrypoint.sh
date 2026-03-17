#!/bin/sh
echo "Misc Configuration..."
mkdir -p /var/log/nginx/

echo "Nginx Set Up Done! Proceeding further..."
exec nginx -g "daemon off;"