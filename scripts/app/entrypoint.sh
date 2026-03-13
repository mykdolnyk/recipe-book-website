#!/bin/sh

echo "Migrating the DB..."
python -u -m flask --app app/run db upgrade

echo "Set Up Done! Proceeding further..."
python -u -m flask --app app/run run --debug --host 0.0.0.0
# exec "$@"