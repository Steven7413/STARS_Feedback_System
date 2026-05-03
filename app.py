from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from flask_socketio import SocketIO, emit, join_room
from pyngrok import ngrok
import time
from datetime import datetime, timedelta
import os
import sys
import subprocess

# Auto-install dependencies if missing
try:
    from fpdf import FPDF
except ImportError:
    print(" * fpdf not found. Please install requirements.txt")
    # No auto-install here to prevent crash loops
    FPDF = None # Soft fail or handle gracefully? Better to let it be missing and fail on usage or rely on batch.
    
# Actually, let's just do standard import. If it fails, the server crashes, but the batch file should have fixed it.
from fpdf import FPDF

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_stars_matrix_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Get IP Address globally for the route to use
start_url_ip = '127.0.0.1'
import socket
try:
    # Connect to an external server (doesn't actually send data) to find outgoing interface
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    start_url_ip = s.getsockname()[0]
    s.close()
except Exception:
    start_url_ip = '127.0.0.1'
    
public_url = None # Placeholder for ngrok if we use it later

import threading
import re

def start_tunnel():
    global public_url
    # Skip tunnel if running permanently in the cloud
    if os.environ.get('RENDER'):
        return
        
    print(" * Requesting secure tunnel via cloudflared...")
    def run_cf():
        global public_url
        try:
            if os.name == 'nt':
                os.system('taskkill /IM cloudflared.exe /F >nul 2>&1')
                time.sleep(1)
                
            exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloudflared.exe')
            if not os.path.exists(exe_path):
                print(" * cloudflared.exe not found.")
                public_url = None
                return

            proc = subprocess.Popen(
                [exe_path, "tunnel", "--url", "http://localhost:5001"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            for line in iter(proc.stdout.readline, ''):
                if not public_url:
                    match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                    if match:
                        public_url = match.group(1)
                        print(f"\n * Secure Public Tunnel Started: {public_url}\n")
        except Exception as e:
            print(f" * Cloudflare Tunnel Error: {e}")
            public_url = None

    t = threading.Thread(target=run_cf, daemon=True)
    t.start()
    
    # Wait max 8 seconds for tunneling to succeed
    for _ in range(40):
        if public_url:
            break
        time.sleep(0.2)
        
    if not public_url:
        print(" * Tunnel did not attach in time, falling back to local network only.")

start_tunnel()

# State for demo purposes
# Structure: { 'neuro_brain': {'Dinosaur': 0, ...}, 'neuro_level': {...}, ... }
# State for demo purposes
# Structure: { 'neuro_brain': {'Dinosaur': 0, ...}, 'neuro_level': {...}, ... }
session_data = {
    'neuro_brain': {},
    'neuro_level': {},
    'owls': {},
    'rft': {},
    'total_responses': 0,
    'start_time': None,
    'end_time': None,
    'is_locked': False,
    'ioa_history': [],  # List of {timestamp, ioa}
    'students': {},     # {sid: {'name': 'Name', 'votes': {cat:val}, 'participated_video': False}}
}
connected_students = set()
global_student_records = {} # {name: {'participated': 0, 'total_score': 0, 'sessions': []}}
import statistics

@app.route('/')
def index():
    # Pass both URLs so the client can toggle
    return render_template('index.html', 
                         server_ip=public_url if public_url else start_url_ip, 
                         local_ip=start_url_ip, 
                         public_url=public_url)

@socketio.on('connect')
def handle_connect():
    # Note: We don't know role yet, so we wait for 'join' to count as student
    print(f"Client connected: {request.sid}")
    emit('update_charts', session_data)
    emit_metrics()

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_students:
        connected_students.remove(request.sid)
        emit_metrics()
    print(f"Client disconnected: {request.sid}")

@socketio.on('join')
def on_join(data):
    role = data.get('role', 'student')
    name = data.get('name', 'Anonymous') # Get Name
    room = role
    join_room(room)
    
    if role == 'student':
        connected_students.add(request.sid)
        # Initialize Student Data
        if request.sid not in session_data['students']:
            session_data['students'][request.sid] = {
                'name': name,
                'votes': {},
                'participated_video': False
            }
        
        if name not in global_student_records:
            global_student_records[name] = {
                'participated': 0,
                'total_score': 0,
                'sessions': [], # Track score per session/video
                'vote_counts': {} # {category: {value: count}}
            }
        emit_metrics()
        
    print(f"Client {request.sid} ({role} - {name}) joined room: {room}")
    emit('status', {'msg': f'Joined as {role}'})
    
    if role == 'instructor':
        emit('update_charts', session_data)
        emit_metrics()

def emit_metrics():
    """Broadcast active student count and total responses to instructors"""
    metrics = {
        'active_students': len(connected_students),
        'total_responses': session_data.get('total_responses', 0),
        'neuro_count': session_data.get('neuro_count', 0),
        'owls_count': session_data.get('owls_count', 0),
        'rft_count': session_data.get('rft_count', 0),
        'aggression_count': session_data.get('aggression_count', 0)
    }
    socketio.emit('update_metrics', metrics, to='instructor')

@socketio.on('feedback_event')
def handle_feedback(data):
    """
    Receives feedback: {category: 'neuro_brain', value: 'Dinosaur'}
    Updates aggregator and broadcasts new totals.
    """
    category = data.get('category')
    value = data.get('value')
    
    if session_data.get('is_locked'):
        return # Ignore feedback if locked

    # Check for auto-lock (fallback if frontend timer fails or tampering)
    if session_data.get('end_time') and time.time() > session_data.get('end_time'):
        session_data['is_locked'] = True
        emit('session_locked', {'msg': 'Session time expired.'}, to='instructor')
        emit('session_locked', {'msg': 'Session time expired.'}, to='student')
        return

    if category and value:
        # Determine Role of Sender
        is_instructor = False
        # If the sender is in the 'instructor' room... strictly speaking we rely on the client role, 
        # but for simplicity let's check our tracking or just handling. 
        # Actually, the client just emits. We need to know WHO sent it.
        # We don't store role in session directly by SID easily without a lookup.
        # But we know students are in session_data['students'].
        
        if request.sid in session_data['students']:
            # It's a student
            student = session_data['students'][request.sid]
            student['votes'][category] = value
            student['participated_video'] = True
                
        else:
            # Assume Instructor (since they aren't in student list)
            is_instructor = True
            # Instructors just help aggregated counts in this mode
            pass

        # Update Aggregates
        if category not in session_data:
            session_data[category] = {}
        
        if value not in session_data[category]:
            session_data[category][value] = 0
            
        session_data[category][value] += 1
        session_data['total_responses'] = session_data.get('total_responses', 0) + 1
        
        # Increment Category Specific Counters
        if category == 'neuro_brain':
            session_data['neuro_count'] = session_data.get('neuro_count', 0) + 1
        elif category == 'owls':
            session_data['owls_count'] = session_data.get('owls_count', 0) + 1
        elif category == 'rft':
            session_data['rft_count'] = session_data.get('rft_count', 0) + 1
        elif category == 'neuro_level': # Aggression
            session_data['aggression_count'] = session_data.get('aggression_count', 0) + 1

        # Calculate IOA for each category
        session_data['ioa_neuro'] = calculate_ioa_score(session_data.get('neuro_brain', {}))
        session_data['ioa_aggression'] = calculate_ioa_score(session_data.get('neuro_level', {}))
        session_data['ioa_owls'] = calculate_ioa_score(session_data.get('owls', {}))
        session_data['ioa_rft'] = calculate_ioa_score(session_data.get('rft', {}))

        # Calculate Overall IOA (Average of active categories)
        active_ioas = []
        if session_data.get('neuro_count', 0) > 0: active_ioas.append(session_data['ioa_neuro'])
        if session_data.get('aggression_count', 0) > 0: active_ioas.append(session_data['ioa_aggression'])
        if session_data.get('owls_count', 0) > 0: active_ioas.append(session_data['ioa_owls'])
        if session_data.get('rft_count', 0) > 0: active_ioas.append(session_data['ioa_rft'])
        
        if active_ioas:
            session_data['ioa_overall'] = int(sum(active_ioas) / len(active_ioas))
        else:
            session_data['ioa_overall'] = 0
            
        # Backward compatibility for the main display if needed, but we updated frontend to separate them
        # We will map 'ioa_overall' to 'ioa' for safety if frontend expects it
        session_data['ioa'] = session_data['ioa_overall']
        
        # Track History for Trend Graph
        session_data['ioa_history'].append({
            'timestamp': time.time(),
            'ioa': session_data['ioa_overall']
        })

        # Broadcast full updated state to instructors
        emit('update_charts', session_data, to='instructor')
        emit_metrics()
        
        # Also emit raw log for the feed
        # Add 'Name' to the feed if available
        sender_name = "Instructor"
        if request.sid in session_data['students']:
            sender_name = session_data['students'][request.sid]['name']
            
        # We modify the data payload to include name for the feed
        feed_data = data.copy()
        feed_data['name'] = sender_name
        emit('student_feedback', feed_data, to='instructor')

@socketio.on('start_session')
def handle_start_session():
    session_data['start_time'] = time.time()
    session_data['end_time'] = time.time() + (8 * 3600) # 8 Hours
    session_data['is_locked'] = False
    session_data['ioa_history'] = []
    
    emit('session_started', {
        'start_time': session_data['start_time'], 
        'end_time': session_data['end_time']
    })
    print("Session STARTED. Ends in 8 hours.")

@socketio.on('extend_session')
def handle_extend_session(data):
    # data: {'minutes': 60} or similar
    minutes = int(data.get('minutes', 60))
    if session_data.get('end_time'):
        session_data['end_time'] += (minutes * 60)
    else:
        # If not started, start now? Or just set end time from now?
        session_data['end_time'] = time.time() + (minutes * 60)
        
    session_data['is_locked'] = False # Unlock if it was locked
    emit('session_extended', {'end_time': session_data['end_time']})
    print(f"Session EXTENDED by {minutes} minutes.")

@app.route('/download_report')
def download_report():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="S.T.A.R.S. Matrix - Clinical IOA Report", ln=1, align='C')
    
    pdf.set_font("Arial", size=10)
    timestamp = session_data.get('start_time')
    if timestamp is None:
        timestamp = time.time()
    start_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    pdf.cell(200, 10, txt=f"Session Start: {start_str}", ln=1, align='C')
    pdf.ln(10)
    
    # Calculate Average IOA from History for the 'Day' score if using history, otherwise current
    history = session_data.get('ioa_history', [])
    if history:
        avg_ioa = int(sum(h['ioa'] for h in history) / len(history))
    else:
        avg_ioa = session_data.get('ioa_overall', 0)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Session Average Reliability (IOA): {avg_ioa}%", ln=1, align='L')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Current Activity Snapshot:", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Neuro IOA: {session_data.get('ioa_neuro', 0)}%", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Aggression IOA: {session_data.get('ioa_aggression', 0)}%", ln=1, align='L')
    pdf.cell(200, 10, txt=f"OWLS IOA: {session_data.get('ioa_owls', 0)}%", ln=1, align='L')
    pdf.cell(200, 10, txt=f"RFT IOA: {session_data.get('ioa_rft', 0)}%", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Total Responses: {session_data.get('total_responses', 0)}", ln=1, align='L')
    
    # Participant Table
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Participant Performance (Global History)", ln=1, align='L')
    
    pdf.set_font("Arial", 'B', 10)
    # Headers
    pdf.cell(80, 10, "Name", 1)
    pdf.cell(40, 10, "Videos Watched", 1)
    pdf.cell(40, 10, "Avg Agreement %", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    
    if not global_student_records:
        pdf.cell(190, 10, "No participants recorded.", 1, ln=1, align='C')
    else:
        for name, data in global_student_records.items():
            participated = data.get('participated', 0)
            sessions = data.get('sessions', [])
            
            avg_score = 0
            if sessions:
                avg_score = int(sum(sessions) / len(sessions))
            
            pdf.cell(80, 10, str(name), 1)
            pdf.cell(40, 10, str(participated), 1)
            pdf.cell(40, 10, f"{avg_score}%", 1)
            pdf.ln()

    # Detailed Analysis Pages
    if global_student_records:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Detailed Participant Analysis", ln=1, align='C')
        pdf.ln(5)

        for name, data in global_student_records.items():
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=f"Participant: {name}", ln=1, align='L')
            
            # Score History
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(200, 6, txt="Session Scores:", ln=1)
            pdf.set_font("Arial", size=10)
            
            sessions = data.get('sessions', [])
            if sessions:
                score_str = " | ".join([f"Video {i+1}: {s}%" for i, s in enumerate(sessions)])
                pdf.multi_cell(0, 6, txt=score_str)
            else:
                pdf.cell(0, 6, txt="No sessions recorded.", ln=1)
            
            pdf.ln(2)

            # Voting Profile
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(200, 6, txt="Voting Profile (Cumulative):", ln=1)
            pdf.set_font("Arial", size=10)

            vote_counts = data.get('vote_counts', {})
            if vote_counts:
                for cat, counts in vote_counts.items():
                    total_cat_votes = sum(counts.values())
                    if total_cat_votes > 0:
                        count_strs = []
                        for val, count in counts.items():
                            pct = int((count / total_cat_votes) * 100)
                            count_strs.append(f"{val}: {pct}%")
                        
                        pdf.set_font("Arial", 'I', 10)
                        pdf.cell(40, 6, txt=f"{cat}: ", border=0)
                        pdf.set_font("Arial", size=10)
                        pdf.cell(0, 6, txt=", ".join(count_strs), ln=1)
            else:
                pdf.cell(0, 6, txt="No votes recorded.", ln=1)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Separator Line
            pdf.ln(5)

    filename = f"IOA_Report_{int(time.time())}.pdf"
    path = os.path.join("static", "reports")
    os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, filename)
    pdf.output(full_path)
    
    from flask import send_file
    return send_file(full_path, as_attachment=True)

def calculate_ioa_score(votes_dict):
    """
    Calculates consensus percentage: (Most Agreed Option / Total Votes) * 100
    """
    if not votes_dict:
        return 0
    total = sum(votes_dict.values())
    if total == 0:
        return 0
    max_agreement = max(votes_dict.values())
    return int((max_agreement / total) * 100)

@socketio.on('reset_session')
def handle_reset():
    global session_data
    # Preserve Session Timer and History
    saved_start = session_data.get('start_time')
    saved_end = session_data.get('end_time')
    saved_history = session_data.get('ioa_history', [])
    
    # GRADING LOGIC BEFORE CLEARING
    # 1. Determine Consensus for each category (Mode)
    consensus = {} 
    categories = ['neuro_brain', 'neuro_level', 'owls', 'rft']
    
    for cat in categories:
        counts = session_data.get(cat, {})
        if counts:
            # Find key with max value
            winner = max(counts, key=counts.get)
            consensus[cat] = winner
            
    # 2. Grade Students
    for sid, stud_data in session_data['students'].items():
        if stud_data.get('participated_video'):
            name = stud_data['name']
            votes = stud_data['votes']
            
            # Update Global Participation
            if name in global_student_records:
                global_student_records[name]['participated'] += 1
                
                # Calculate Score for this video
                # Logic: Average % of categories matched against consensus
                matches = 0
                possible = 0
                
                for cat, correct_val in consensus.items():
                    if cat in votes: 
                        # Update Cumulative Vote Counts
                        if cat not in global_student_records[name]['vote_counts']:
                            global_student_records[name]['vote_counts'][cat] = {}
                        
                        val_chosen = votes[cat]
                        if val_chosen not in global_student_records[name]['vote_counts'][cat]:
                            global_student_records[name]['vote_counts'][cat][val_chosen] = 0
                        global_student_records[name]['vote_counts'][cat][val_chosen] += 1

                        # Grade
                        if votes.get(cat) == correct_val:
                            matches += 1
                        possible += 1
                
                session_score = 0
                if possible > 0:
                    session_score = int((matches / possible) * 100)
                
                global_student_records[name]['sessions'].append(session_score)
                print(f"Graded {name}: {session_score}% (Match {matches}/{possible})")

    session_data = {
        'neuro_brain': {},
        'neuro_level': {},
        'owls': {},
        'rft': {},
        'total_responses': 0,
        'neuro_count': 0,
        'owls_count': 0,
        'rft_count': 0,
        'aggression_count': 0,
        'ioa': 0,
        'ioa_overall': 0,
        'ioa_neuro': 0,
        'ioa_aggression': 0,
        'ioa_owls': 0,
        'ioa_rft': 0,
        'start_time': saved_start,
        'end_time': saved_end,
        'is_locked': False,
        'ioa_history': saved_history,
        'students': {} # Cleared for next video
    }
    print("Session Reset (Timer Continues)")
    emit('update_charts', session_data, to='instructor')
    emit_metrics()
    emit('session_reset', {'msg': 'Session data cleared'}, to='instructor')

if __name__ == '__main__':
    # IP is already calculated globally as start_url_ip

    print(f" * S.T.A.R.S. MATRIX is running!")
    print(f" * Instructor Link: http://localhost:5001")
    print(f" * Student Link:    http://{start_url_ip}:5001")
    
    # Auto-open browser only if running locally
    if not os.environ.get('RENDER'):
        import webbrowser
        from threading import Timer
        Timer(1.5, lambda: webbrowser.open('http://localhost:5001')).start()

    # Bind to Render's dynamic port, or fallback to 5001 locally
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)

