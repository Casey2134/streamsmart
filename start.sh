#!/bin/bash
set -e

# Start Tailscale daemon in userspace mode (works in containers without root)
if [ -n "$TAILSCALE_AUTHKEY" ]; then
    echo "Starting Tailscale..."
    mkdir -p /var/lib/tailscale /var/run/tailscale
    tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock --tun=userspace-networking &
    sleep 3
    tailscale up --authkey="$TAILSCALE_AUTHKEY" --hostname="streamsmart-railway"
    echo "Tailscale connected!"
    tailscale status
else
    echo "Warning: TAILSCALE_AUTHKEY not set, skipping Tailscale connection"
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Start Celery worker in background (if CELERY_BROKER_URL is set)
if [ -n "$CELERY_BROKER_URL" ]; then
    echo "Starting Celery worker..."
    celery -A streamsmart worker -l info &
fi

# Start the server
echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p ${PORT:-8000} streamsmart.asgi:application
