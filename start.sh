#!/bin/bash
set -e

# Start Tailscale daemon in userspace mode with SOCKS5 proxy
if [ -n "$TAILSCALE_AUTHKEY" ]; then
    mkdir -p /var/lib/tailscale /var/run/tailscale
    tailscaled --state=/var/lib/tailscale/tailscaled.state \
               --socket=/var/run/tailscale/tailscaled.sock \
               --tun=userspace-networking \
               --socks5-server=localhost:1055 &
    sleep 3
    tailscale up --authkey="$TAILSCALE_AUTHKEY" --hostname="streamsmart-railway" 2>/dev/null
    export TAILSCALE_PROXY=socks5://localhost:1055
fi

# Run migrations
python manage.py migrate --no-input

# Start Celery worker in background
if [ -n "$CELERY_BROKER_URL" ]; then
    celery -A streamsmart worker -l warning &
fi

# Start the server
exec daphne -b 0.0.0.0 -p ${PORT:-8000} streamsmart.asgi:application
