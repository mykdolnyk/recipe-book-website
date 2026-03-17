#!/bin/sh

echo "Migrating the DB..."
python -u -m flask --app app/run db upgrade

echo "Misc Configuration..."
mkdir -p /var/log/web/

echo "Preparing Static Files..."
mkdir -p staticfiles
cp -r static/* staticfiles/

echo "Web App Set Up Done! Proceeding further..."
exec "$@"