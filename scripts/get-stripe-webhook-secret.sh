#!/bin/bash
# Script to extract the Stripe webhook signing secret from docker logs

echo "Fetching Stripe webhook signing secret from docker logs..."
echo ""

# Get the container name based on docker-compose setup
CONTAINER_NAME=$(docker ps --filter "name=stripe-cli" --format "{{.Names}}" | head -1)

if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ Error: Stripe CLI container is not running"
    echo ""
    echo "Please start it with:"
    echo "  docker-compose up stripe-cli"
    echo "or"
    echo "  docker-compose up -d stripe-cli"
    exit 1
fi

echo "📦 Container: $CONTAINER_NAME"
echo ""

# Extract the webhook secret from logs
WEBHOOK_SECRET=$(docker logs "$CONTAINER_NAME" 2>&1 | grep -oP 'whsec_[a-zA-Z0-9]+' | head -1)

if [ -z "$WEBHOOK_SECRET" ]; then
    echo "⚠️  Webhook secret not found yet. The container might still be starting..."
    echo ""
    echo "Run this command to see the logs:"
    echo "  docker logs -f $CONTAINER_NAME"
    exit 1
fi

echo "✅ Webhook Signing Secret Found!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$WEBHOOK_SECRET"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Add this to your .env file:"
echo "STRIPE_WEBHOOK_SECRET=$WEBHOOK_SECRET"
echo ""
echo "Or update it automatically (backup your .env first!):"
echo "  sed -i 's/^STRIPE_WEBHOOK_SECRET=.*/STRIPE_WEBHOOK_SECRET=$WEBHOOK_SECRET/' .env"
