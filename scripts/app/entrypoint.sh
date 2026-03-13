#!/bin/sh

echo "Migrating the DB..."
python -u -m flask --app app/run db upgrade

echo "Set Up Done! Proceeding further..."
exec "$@"