import sys
import subprocess
import traceback
import time

def log(msg):
    print(msg)
    with open("startup_log.txt", "a") as f:
        f.write(msg + "\n")

def install(package):
    log(f" * Installing missing requirement: {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        log(f" * Installed {package}")
    except Exception as e:
        log(f" ! Failed to install {package}: {e}")
        raise e

def main():
    # Clear log
    with open("startup_log.txt", "w") as f:
        f.write("Starting Launcher...\n")
        
    log(" * S.T.A.R.S. MATRIX Launcher Initializing...")
    
    # Check for critical dependencies
    required = ['flask', 'flask_socketio', 'eventlet', 'pyngrok', 'fpdf']
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            try:
                install(package)
            except Exception as e:
                log(f"   Please install manually or check your internet connection.")
                return

    log(" * All dependencies checked.")
    log(" * Starting application logic...")
    
    try:
        # Run app.py
        log(" * Executing app.py...")
        with open("startup_log.txt", "a") as f:
            # We want output to go to BOTH console and file if possible, 
            # but for simplicity, let's let it inherit stdout (so user sees it) 
            # and seemingly we can't easily tee it without threading.
            # Let's just run it. If it crashes, usually the error prints to stderr.
            # We can try to capture stderr.
             process = subprocess.Popen([sys.executable, 'app.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
             
             # Stream output to console and file
             for line in process.stdout:
                 print(line, end='')
                 f.write(line)
                 f.flush()
             
             process.wait()
             if process.returncode != 0:
                 raise subprocess.CalledProcessError(process.returncode, 'app.py')

    except subprocess.CalledProcessError as e:
        log(f" ! Application crashed with exit code {e.returncode}")
    except KeyboardInterrupt:
        log("\n * User stopped the server.")
    except Exception:
        log(" ! Critical Error:")
        with open("startup_log.txt", "a") as f:
            traceback.print_exc(file=f)

    except Exception:
        with open("startup_log.txt", "a") as f:
            traceback.print_exc(file=f)

def add_firewall_rule():
    """Attempts to add a firewall rule for the current Python executable."""
    try:
        exe_path = sys.executable
        log(f" * Attempting to whitelist Python in Firewall: {exe_path}")
        
        # PowerShell command to add rule for the application
        cmd = f"New-NetFirewallRule -DisplayName 'STARS Matrix Python' -Direction Inbound -Program '{exe_path}' -Action Allow -Force"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        log(" * Firewall rule command executed.")
    except Exception as e:
        log(f" ! Firewall Setup Error (Ignore if not Admin): {e}")

def kill_zombies():
    """Kills lingering python and ngrok processes."""
    log(" * Cleaning up background processes...")
    try:
        # We need to be careful not to kill OURSELVES. 
        # But since we are 'start_server.py', killing 'python.exe' might kill us if we assume name matching.
        # So we only kill ngrok here. The batch file handles python killing before we start.
        subprocess.run(["taskkill", "/IM", "cloudflared.exe", "/F"], capture_output=True)
    except:
        pass

if __name__ == "__main__":
    try:
        kill_zombies()
        add_firewall_rule()
        main()
    except Exception:
        with open("startup_log.txt", "a") as f:
            traceback.print_exc(file=f)
