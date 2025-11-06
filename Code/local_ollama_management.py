import os
import subprocess
import psutil
from config import OLLAMA_PATH

# Ollama server management

def start_ollama():
    """Start the Ollama server if it's not already running."""
    print("\nStarting Ollama server...")
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.Popen([OLLAMA_PATH, 'serve'], stdout=devnull, stderr=devnull)
        print("Ollama server started.")
    except Exception as e:
        print(f"Failed to initiate Ollama: {e}")


def is_ollama_running() -> bool:
    """Check if the Ollama server is running."""
    print("Checking if Ollama server is running...")
    isRunning = any('ollama' in proc.info['name'].lower() for proc in psutil.process_iter(['name']))
    print(isRunning)
    return isRunning


def terminate_ollama_processes():
    """Terminate all running Ollama processes."""
    print("\n\nTerminating Ollama process...")
    for proc in psutil.process_iter(['pid', 'name']):
        if 'ollama' in proc.info['name'].lower():  
            proc.terminate() 
            proc.wait() 
            print(f"Ollama Process (PID {proc.info['pid']}) terminated")