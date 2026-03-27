#!/bin/bash
set -e

echo "Starting RadiomicsHub Backend..."

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z postgres 5432; do
  sleep 0.5
done
echo "Database is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.5
done
echo "Redis is ready!"

# Wait for MinIO
echo "Waiting for MinIO..."
while ! nc -z minio 9000; do
  sleep 0.5
done
echo "MinIO is ready!"

# Run database initialization
echo "Initializing database..."
python /app/scripts/init_db.py

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000