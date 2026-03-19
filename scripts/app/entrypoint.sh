#!/bin/sh

echo "Creating Dirs and Files..."
mkdir -p /var/log/web/
touch /var/log/web/error.log

echo "Migrating the DB..."
until nc -z db 5432; do
    echo "- Waiting for Postgres..."
    sleep 1
done
echo "Postgres is ready!"
python -u -m flask --app app/run db upgrade

echo "Preparing Static Files..."
mkdir -p staticfiles
cp -r static/* staticfiles/

echo "Web App Set Up Done! Proceeding further..."
exec "$@"