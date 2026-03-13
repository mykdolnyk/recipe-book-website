#!/bin/sh

echo "Migrating the DB..."
python -u -m flask --app app/run db upgrade

echo "Misc Configuration..."
mkdir /var/log/web/

echo "Web App Set Up Done! Proceeding further..."
exec "$@"