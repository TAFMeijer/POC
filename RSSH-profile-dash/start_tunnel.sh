#!/bin/bash

echo "=================================================="
echo "Starting RSSH Profile Dashboard & Cloudflare Tunnel"
echo "=================================================="

# Default domain configuration
DOMAIN="global-health-data.org"
ROUTING_PATH="HealthSystemIndicators"
TUNNEL_NAME="rssh-dash"
PORT=8050

# Ensure cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "Error: cloudflared is not installed. Please run 'brew install cloudflared' first."
    exit 1
fi

echo -e "\n[1/4] Checking Cloudflare Authentication..."
# Check if a cert already exists, if not prompt login
if [ ! -f ~/.cloudflared/cert.pem ]; then
    echo "No Cloudflare certificate found. Opening browser for login..."
    cloudflared tunnel login
fi

echo -e "\n[2/4] Setting up Tunnel ($TUNNEL_NAME)..."
# Check if tunnel already exists
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "Tunnel '$TUNNEL_NAME' already exists."
    # Extract existing UUID cleanly (head -n 1 to prevent multiline capture)
    TUNNEL_UUID=$(cloudflared tunnel list | grep -w "$TUNNEL_NAME" | head -n 1 | awk '{print $1}')
else
    echo "Creating new tunnel '$TUNNEL_NAME'..."
    # Create tunnel and grep the UUID from the output
    CREATE_OUTPUT=$(cloudflared tunnel create "$TUNNEL_NAME" 2>&1)
    TUNNEL_UUID=$(echo "$CREATE_OUTPUT" | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
    echo "Tunnel created with UUID: $TUNNEL_UUID"
fi

echo "Forcing DNS route to $DOMAIN..."
cloudflared tunnel route dns -f "$TUNNEL_NAME" "$DOMAIN"

echo -e "\n[3/4] Configuring Routing Rules..."
# Create the local config file for the routing logic
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/$TUNNEL_NAME-config.yml << EOL
tunnel: $TUNNEL_UUID
credentials-file: $HOME/.cloudflared/$TUNNEL_UUID.json

ingress:
  # Route the specific path to your local Python server
  - hostname: $DOMAIN
    path: /$ROUTING_PATH.*
    service: http://127.0.0.1:$PORT
  
  # Catch-all rule to prevent exposing your Mac
  - service: http_status:404
EOL

echo -e "\n[4/4] Starting Services..."

# Start the Plotly Dash app in the background
echo "Starting Python Dashboard (app.py) on Port $PORT..."
python app.py &
APP_PID=$!

# Give the app a few seconds to boot up
sleep 3
echo -e "\nDashboard is starting locally. Establishing Cloudflare edge connection..."
echo -e "Your dashboard will be publicly available at: https://$DOMAIN/$ROUTING_PATH/\n"
echo "Press CTRL+C at any time to shut down both the tunnel and the dashboard."

# Trap CTRL+C (SIGINT) to clean up the python process when user quits
trap "echo -e '\nShutting down dashboard...'; kill $APP_PID; exit" INT

# Run the tunnel in the foreground
cloudflared tunnel --config ~/.cloudflared/$TUNNEL_NAME-config.yml run "$TUNNEL_NAME"
