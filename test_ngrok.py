from pyngrok import ngrok
import sys

print("Starting Ngrok Check...", fluid=True)
try:
    ngrok.set_auth_token("38OfonLs2VAtzEZh59IMa3UhfPO_6jhT1CsyFs8T77ifAzJGK")
    print("Auth token set.", flush=True)
    
    # Kill existing tunnels?
    ngrok.kill()
    
    tunnel = ngrok.connect(5000)
    print(f"Tunnel URL: {tunnel.public_url}", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
