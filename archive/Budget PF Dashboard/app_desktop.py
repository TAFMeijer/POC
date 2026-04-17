import webview
from app import app
import threading
import time

def run_dash():
    # Run the dash application
    # Using 127.0.0.1, we disable debug because hot-reloading clashes with threads
    app.run(debug=False, port=8000, host="127.0.0.1")

if __name__ == '__main__':
    # Start the web server in a background thread
    t = threading.Thread(target=run_dash)
    t.daemon = True
    t.start()
    
    # Wait for the server to spin up
    time.sleep(2)
    
    # Create a native window that bypasses standard browser network layers
    webview.create_window(
        'RSSH Budget PF Dashboard', 
        'http://127.0.0.1:8000/budget-pf-poc/',
        width=1400,
        height=900,
        min_size=(1000, 600)
    )
    
    # Start the desktop app UI loop
    webview.start()
