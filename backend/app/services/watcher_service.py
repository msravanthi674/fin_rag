import time
import threading
import os

# Simulated alert system for SEC filings
active_watchlists = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"]

def start_watcher():
    def _run():
        while True:
            # Mocking a new filing discovery
            # In a real scenario, this would poll sec.gov/edgar/search
            print(f"[Watcher] Checking filings for: {active_watchlists}")
            time.sleep(300) # Check every 5 minutes

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    start_watcher()
    print("Watcher started.")
