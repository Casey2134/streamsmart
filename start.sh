#!/bin/bash
set -e

# Start Tailscale daemon in userspace mode with SOCKS5 proxy
if [ -n "$TAILSCALE_AUTHKEY" ]; then
    echo "Starting Tailscale..."
    mkdir -p /var/lib/tailscale /var/run/tailscale

    # Start tailscaled with SOCKS5 proxy on port 1055
    tailscaled --state=/var/lib/tailscale/tailscaled.state \
               --socket=/var/run/tailscale/tailscaled.sock \
               --tun=userspace-networking \
               --socks5-server=localhost:1055 &

    sleep 3
    tailscale up --authkey="$TAILSCALE_AUTHKEY" --hostname="streamsmart-railway"
    echo "Tailscale connected!"
    tailscale status

    # Set proxy environment variables for Python requests
    export ALL_PROXY=socks5://localhost:1055
    export HTTPS_PROXY=socks5://localhost:1055
    export HTTP_PROXY=socks5://localhost:1055
    echo "SOCKS5 proxy configured on localhost:1055"
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
