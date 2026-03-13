#!/bin/sh
echo "Misc Configuration..."
mkdir /var/log/nginx/

echo "Nginx Set Up Done! Proceeding further..."
exec nginx -g "daemon off;"