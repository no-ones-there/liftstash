from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

DATABASE = os.environ.get('DATABASE', 'workout_tracker.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Ensure data directory exists
    db_dir = os.path.dirname(DATABASE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    with get_db() as conn:
        # Add missing columns to existing tables
        try:
            conn.execute('ALTER TABLE exercises ADD COLUMN improvement_direction TEXT DEFAULT "increase"')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            conn.execute('ALTER TABLE exercises ADD COLUMN split_tracking INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            conn.execute('ALTER TABLE program_exercises ADD COLUMN target_sets INTEGER DEFAULT 3')
            conn.execute('ALTER TABLE program_exercises ADD COLUMN target_reps INTEGER DEFAULT 10')
        except sqlite3.OperationalError:
            pass  # Columns already exist
        
        try:
            conn.execute('ALTER TABLE workout_sets ADD COLUMN side TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                muscle_group TEXT,
                improvement_direction TEXT DEFAULT 'increase',
                split_tracking INTEGER DEFAULT 0,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            
            CREATE TABLE IF NOT EXISTS programs (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            
            CREATE TABLE IF NOT EXISTS program_exercises (
                id INTEGER PRIMARY KEY,
                program_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                order_index INTEGER NOT NULL,
                target_sets INTEGER DEFAULT 3,
                target_reps INTEGER DEFAULT 10,
                FOREIGN KEY (program_id) REFERENCES programs (id),
                FOREIGN KEY (exercise_id) REFERENCES exercises (id)
            );
            
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY,
                program_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                notes TEXT,
                FOREIGN KEY (program_id) REFERENCES programs (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            
            CREATE TABLE IF NOT EXISTS workout_sets (
                id INTEGER PRIMARY KEY,
                workout_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                set_number INTEGER NOT NULL,
                weight REAL,
                reps INTEGER,
                side TEXT,
                FOREIGN KEY (workout_id) REFERENCES workouts (id),
                FOREIGN KEY (exercise_id) REFERENCES exercises (id)
            );
            
            CREATE TABLE IF NOT EXISTS personal_records (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                weight REAL NOT NULL,
                reps INTEGER NOT NULL,
                date DATE NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (exercise_id) REFERENCES exercises (id)
            );
        ''')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
        if user and user['password_hash'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db() as conn:
            try:
                conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                           (username, hash_password(password)))
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                return render_template('register.html', error='Username already exists')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/exercises')
def exercises():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        exercises = conn.execute('''
            SELECT * FROM exercises 
            WHERE user_id = ? OR user_id IS NULL 
            ORDER BY name
        ''', (session['user_id'],)).fetchall()
    
    return render_template('exercises.html', exercises=exercises)

@app.route('/add_exercise', methods=['POST'])
def add_exercise():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    name = request.form['name']
    muscle_group = request.form['muscle_group']
    improvement_direction = request.form.get('improvement_direction', 'increase')
    split_tracking = 1 if request.form.get('split_tracking') else 0
    
    with get_db() as conn:
        conn.execute('INSERT INTO exercises (name, muscle_group, improvement_direction, split_tracking, user_id) VALUES (?, ?, ?, ?, ?)',
                    (name, muscle_group, improvement_direction, split_tracking, session['user_id']))
    
    return redirect(url_for('exercises'))

@app.route('/workouts')
def workouts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        workouts = conn.execute('''
            SELECT w.*, p.name as program_name 
            FROM workouts w
            JOIN programs p ON w.program_id = p.id
            WHERE w.user_id = ?
            ORDER BY w.date DESC
        ''', (session['user_id'],)).fetchall()
    
    return render_template('workouts.html', workouts=workouts)

@app.route('/workout/<int:workout_id>')
def workout_detail(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        workout = conn.execute('''
            SELECT w.*, p.name as program_name 
            FROM workouts w
            JOIN programs p ON w.program_id = p.id
            WHERE w.id = ? AND w.user_id = ?
        ''', (workout_id, session['user_id'])).fetchone()
        
        program_exercises = conn.execute('''
            SELECT e.id, e.name, pe.target_sets, pe.target_reps, e.split_tracking
            FROM program_exercises pe
            JOIN exercises e ON pe.exercise_id = e.id
            WHERE pe.program_id = ?
            ORDER BY pe.order_index
        ''', (workout['program_id'],)).fetchall()
        
        sets = conn.execute('''
            SELECT ws.*, e.name as exercise_name
            FROM workout_sets ws
            JOIN exercises e ON ws.exercise_id = e.id
            WHERE ws.workout_id = ?
            ORDER BY e.name, ws.side, ws.set_number
        ''', (workout_id,)).fetchall()
    
    return render_template('workout_detail.html', workout=workout, program_exercises=program_exercises, sets=sets)

@app.route('/new_workout', methods=['GET', 'POST'])
def new_workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        program_id = request.form['program_id']
        workout_date = request.form['date']
        notes = request.form.get('notes', '')
        
        with get_db() as conn:
            cursor = conn.execute('''
                INSERT INTO workouts (program_id, user_id, date, notes)
                VALUES (?, ?, ?, ?)
            ''', (program_id, session['user_id'], workout_date, notes))
            workout_id = cursor.lastrowid
        
        return redirect(url_for('workout_detail', workout_id=workout_id))
    
    with get_db() as conn:
        programs = conn.execute('SELECT * FROM programs WHERE user_id = ?', 
                               (session['user_id'],)).fetchall()
    
    return render_template('new_workout.html', programs=programs, today=date.today())

@app.route('/add_set', methods=['POST'])
def add_set():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    workout_id = request.json['workout_id']
    exercise_id = request.json['exercise_id']
    weight = request.json['weight']
    reps = request.json['reps']
    side = request.json.get('side')
    
    with get_db() as conn:
        # Get next set number for this side
        if side:
            set_number = conn.execute('''
                SELECT COALESCE(MAX(set_number), 0) + 1 
                FROM workout_sets 
                WHERE workout_id = ? AND exercise_id = ? AND side = ?
            ''', (workout_id, exercise_id, side)).fetchone()[0]
        else:
            set_number = conn.execute('''
                SELECT COALESCE(MAX(set_number), 0) + 1 
                FROM workout_sets 
                WHERE workout_id = ? AND exercise_id = ? AND side IS NULL
            ''', (workout_id, exercise_id)).fetchone()[0]
        
        conn.execute('''
            INSERT INTO workout_sets (workout_id, exercise_id, set_number, weight, reps, side)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (workout_id, exercise_id, set_number, weight, reps, side))
        
        # Check for PR based on exercise improvement direction
        exercise = conn.execute('SELECT improvement_direction FROM exercises WHERE id = ?', (exercise_id,)).fetchone()
        
        if exercise['improvement_direction'] == 'increase':
            pr = conn.execute('''
                SELECT MAX(weight) as best_weight FROM workout_sets ws
                JOIN workouts w ON ws.workout_id = w.id
                WHERE w.user_id = ? AND ws.exercise_id = ? AND ws.reps >= ?
            ''', (session['user_id'], exercise_id, reps)).fetchone()
            is_pr = not pr['best_weight'] or weight > pr['best_weight']
        else:
            pr = conn.execute('''
                SELECT MIN(weight) as best_weight FROM workout_sets ws
                JOIN workouts w ON ws.workout_id = w.id
                WHERE w.user_id = ? AND ws.exercise_id = ? AND ws.reps >= ?
            ''', (session['user_id'], exercise_id, reps)).fetchone()
            is_pr = not pr['best_weight'] or weight < pr['best_weight']
        
        if is_pr:
            conn.execute('''
                INSERT OR REPLACE INTO personal_records (user_id, exercise_id, weight, reps, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], exercise_id, weight, reps, date.today()))
    
    return jsonify({'success': True})

@app.route('/programs')
def programs():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        programs_data = []
        programs = conn.execute('SELECT * FROM programs WHERE user_id = ?', 
                               (session['user_id'],)).fetchall()
        
        for program in programs:
            exercises = conn.execute('''
                SELECT e.name, pe.target_sets, pe.target_reps
                FROM program_exercises pe
                JOIN exercises e ON pe.exercise_id = e.id
                WHERE pe.program_id = ?
                ORDER BY pe.order_index
            ''', (program['id'],)).fetchall()
            
            programs_data.append({
                'program': program,
                'exercises': [f"{ex['name']} ({ex['target_sets']}x{ex['target_reps']})" for ex in exercises]
            })
    
    return render_template('programs.html', programs_data=programs_data)

@app.route('/new_program', methods=['GET', 'POST'])
def new_program():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        exercise_ids = request.form.getlist('exercise_ids')
        target_sets = request.form.getlist('target_sets')
        target_reps = request.form.getlist('target_reps')
        
        with get_db() as conn:
            cursor = conn.execute('INSERT INTO programs (name, description, user_id) VALUES (?, ?, ?)',
                                (name, description, session['user_id']))
            program_id = cursor.lastrowid
            
            for i, exercise_id in enumerate(exercise_ids):
                if exercise_id:
                    sets = int(target_sets[i]) if i < len(target_sets) and target_sets[i] else 3
                    reps = int(target_reps[i]) if i < len(target_reps) and target_reps[i] else 10
                    conn.execute('INSERT INTO program_exercises (program_id, exercise_id, order_index, target_sets, target_reps) VALUES (?, ?, ?, ?, ?)',
                               (program_id, exercise_id, i, sets, reps))
        
        return redirect(url_for('programs'))
    
    with get_db() as conn:
        exercises = conn.execute('''
            SELECT * FROM exercises 
            WHERE user_id = ? OR user_id IS NULL 
            ORDER BY name
        ''', (session['user_id'],)).fetchall()
    
    return render_template('new_program.html', exercises=exercises)

@app.route('/prs')
def personal_records():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        # Get all exercises with workout data for this user
        exercises = conn.execute('''
            SELECT DISTINCT e.id, e.name, e.improvement_direction
            FROM exercises e
            JOIN workout_sets ws ON e.id = ws.exercise_id
            JOIN workouts w ON ws.workout_id = w.id
            WHERE w.user_id = ?
            ORDER BY e.name
        ''', (session['user_id'],)).fetchall()
        
        prs = []
        for exercise in exercises:
            if exercise['improvement_direction'] == 'increase':
                # Find max weight for each rep count
                records = conn.execute('''
                    SELECT ws.weight, ws.reps, w.date
                    FROM workout_sets ws
                    JOIN workouts w ON ws.workout_id = w.id
                    WHERE w.user_id = ? AND ws.exercise_id = ?
                    AND ws.weight = (
                        SELECT MAX(ws2.weight)
                        FROM workout_sets ws2
                        JOIN workouts w2 ON ws2.workout_id = w2.id
                        WHERE w2.user_id = ? AND ws2.exercise_id = ? AND ws2.reps = ws.reps
                    )
                    GROUP BY ws.reps
                    ORDER BY ws.reps DESC
                ''', (session['user_id'], exercise['id'], session['user_id'], exercise['id'])).fetchall()
            else:
                # Find min weight for each rep count (assisted exercises)
                records = conn.execute('''
                    SELECT ws.weight, ws.reps, w.date
                    FROM workout_sets ws
                    JOIN workouts w ON ws.workout_id = w.id
                    WHERE w.user_id = ? AND ws.exercise_id = ?
                    AND ws.weight = (
                        SELECT MIN(ws2.weight)
                        FROM workout_sets ws2
                        JOIN workouts w2 ON ws2.workout_id = w2.id
                        WHERE w2.user_id = ? AND ws2.exercise_id = ? AND ws2.reps = ws.reps
                    )
                    GROUP BY ws.reps
                    ORDER BY ws.reps DESC
                ''', (session['user_id'], exercise['id'], session['user_id'], exercise['id'])).fetchall()
            
            for record in records:
                prs.append({
                    'exercise_name': exercise['name'],
                    'improvement_direction': exercise['improvement_direction'],
                    'best_weight': record['weight'],
                    'reps': record['reps'],
                    'date': record['date']
                })
    
    return render_template('prs.html', prs=prs)

@app.route('/api/exercises')
def api_exercises():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    with get_db() as conn:
        exercises = conn.execute('''
            SELECT * FROM exercises 
            WHERE user_id = ? OR user_id IS NULL 
            ORDER BY name
        ''', (session['user_id'],)).fetchall()
    
    return jsonify([dict(ex) for ex in exercises])

@app.route('/api/create_exercise', methods=['POST'])
def api_create_exercise():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    name = data.get('name')
    muscle_group = data.get('muscle_group', '')
    improvement_direction = data.get('improvement_direction', 'increase')
    split_tracking = 1 if data.get('split_tracking') else 0
    
    if not name:
        return jsonify({'error': 'Exercise name required'}), 400
    
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO exercises (name, muscle_group, improvement_direction, split_tracking, user_id) VALUES (?, ?, ?, ?, ?)',
            (name, muscle_group, improvement_direction, split_tracking, session['user_id'])
        )
        exercise_id = cursor.lastrowid
    
    return jsonify({'success': True, 'exercise_id': exercise_id})

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        exercises = conn.execute('''
            SELECT DISTINCT e.id, e.name
            FROM exercises e
            JOIN workout_sets ws ON e.id = ws.exercise_id
            JOIN workouts w ON ws.workout_id = w.id
            WHERE w.user_id = ?
            ORDER BY e.name
        ''', (session['user_id'],)).fetchall()
    
    return render_template('history.html', exercises=exercises)

@app.route('/api/exercise_history')
def api_exercise_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    exercise_ids = request.args.getlist('exercise_ids')
    if not exercise_ids:
        return jsonify([])
    
    with get_db() as conn:
        data = []
        for exercise_id in exercise_ids:
            exercise = conn.execute('SELECT name, improvement_direction FROM exercises WHERE id = ?', (exercise_id,)).fetchone()
            
            history = conn.execute('''
                SELECT w.date, MAX(ws.weight) as max_weight
                FROM workout_sets ws
                JOIN workouts w ON ws.workout_id = w.id
                WHERE w.user_id = ? AND ws.exercise_id = ?
                GROUP BY w.date
                ORDER BY w.date
            ''', (session['user_id'], exercise_id)).fetchall()
            
            data.append({
                'exercise_id': exercise_id,
                'exercise_name': exercise['name'],
                'improvement_direction': exercise['improvement_direction'],
                'data': [{'date': h['date'], 'weight': h['max_weight']} for h in history]
            })
    
    return jsonify(data)

# Edit and Delete Routes
@app.route('/edit_exercise/<int:exercise_id>', methods=['POST'])
def edit_exercise(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    name = request.form['name']
    muscle_group = request.form['muscle_group']
    improvement_direction = request.form.get('improvement_direction', 'increase')
    split_tracking = 1 if request.form.get('split_tracking') else 0
    
    with get_db() as conn:
        conn.execute('UPDATE exercises SET name = ?, muscle_group = ?, improvement_direction = ?, split_tracking = ? WHERE id = ? AND user_id = ?',
                    (name, muscle_group, improvement_direction, split_tracking, exercise_id, session['user_id']))
    
    return redirect(url_for('exercises'))

@app.route('/delete_exercise/<int:exercise_id>', methods=['POST'])
def delete_exercise(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        conn.execute('DELETE FROM exercises WHERE id = ? AND user_id = ?', (exercise_id, session['user_id']))
    
    return redirect(url_for('exercises'))

@app.route('/edit_program/<int:program_id>', methods=['GET', 'POST'])
def edit_program(program_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        program = conn.execute('SELECT * FROM programs WHERE id = ? AND user_id = ?', 
                              (program_id, session['user_id'])).fetchone()
        if not program:
            return redirect(url_for('programs'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        exercise_ids = request.form.getlist('exercise_ids')
        target_sets = request.form.getlist('target_sets')
        target_reps = request.form.getlist('target_reps')
        
        with get_db() as conn:
            conn.execute('UPDATE programs SET name = ?, description = ? WHERE id = ?',
                        (name, description, program_id))
            
            conn.execute('DELETE FROM program_exercises WHERE program_id = ?', (program_id,))
            
            for i, exercise_id in enumerate(exercise_ids):
                if exercise_id:
                    sets = int(target_sets[i]) if i < len(target_sets) and target_sets[i] else 3
                    reps = int(target_reps[i]) if i < len(target_reps) and target_reps[i] else 10
                    conn.execute('INSERT INTO program_exercises (program_id, exercise_id, order_index, target_sets, target_reps) VALUES (?, ?, ?, ?, ?)',
                               (program_id, exercise_id, i, sets, reps))
        
        return redirect(url_for('programs'))
    
    with get_db() as conn:
        exercises = conn.execute('''
            SELECT * FROM exercises 
            WHERE user_id = ? OR user_id IS NULL 
            ORDER BY name
        ''', (session['user_id'],)).fetchall()
        
        program_exercises = conn.execute('''
            SELECT pe.*, e.name as exercise_name
            FROM program_exercises pe
            JOIN exercises e ON pe.exercise_id = e.id
            WHERE pe.program_id = ?
            ORDER BY pe.order_index
        ''', (program_id,)).fetchall()
    
    return render_template('edit_program.html', program=program, exercises=exercises, program_exercises=program_exercises)

@app.route('/delete_program/<int:program_id>', methods=['POST'])
def delete_program(program_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        conn.execute('DELETE FROM programs WHERE id = ? AND user_id = ?', (program_id, session['user_id']))
    
    return redirect(url_for('programs'))

@app.route('/edit_workout/<int:workout_id>', methods=['GET', 'POST'])
def edit_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        workout = conn.execute('SELECT * FROM workouts WHERE id = ? AND user_id = ?', 
                              (workout_id, session['user_id'])).fetchone()
        if not workout:
            return redirect(url_for('workouts'))
    
    if request.method == 'POST':
        workout_date = request.form['date']
        notes = request.form.get('notes', '')
        
        with get_db() as conn:
            conn.execute('UPDATE workouts SET date = ?, notes = ? WHERE id = ?',
                        (workout_date, notes, workout_id))
        
        return redirect(url_for('workout_detail', workout_id=workout_id))
    
    return render_template('edit_workout.html', workout=workout)

@app.route('/delete_workout/<int:workout_id>', methods=['POST'])
def delete_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        conn.execute('DELETE FROM workouts WHERE id = ? AND user_id = ?', (workout_id, session['user_id']))
    
    return redirect(url_for('workouts'))

@app.route('/delete_set/<int:set_id>', methods=['POST'])
def delete_set(set_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    with get_db() as conn:
        # Verify ownership
        set_data = conn.execute('''
            SELECT ws.workout_id FROM workout_sets ws
            JOIN workouts w ON ws.workout_id = w.id
            WHERE ws.id = ? AND w.user_id = ?
        ''', (set_id, session['user_id'])).fetchone()
        
        if set_data:
            conn.execute('DELETE FROM workout_sets WHERE id = ?', (set_id,))
            return jsonify({'success': True})
    
    return jsonify({'error': 'Set not found'}), 404

# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)