import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    conn = sqlite3.connect('task_manager.db')
    c = conn.cursor()
    
    # Create the tasks table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TEXT,
            notes TEXT,
            start_time TEXT,
            elapsed_time INTEGER DEFAULT 0,
            is_completed BOOLEAN DEFAULT 0,
            progress INTEGER DEFAULT 0
        )
    ''')
    
    # Add progress column if it doesn't exist
    try:
        c.execute('ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        # Column already exists, ignore the error
        pass
    
    conn.commit()
    conn.close()
    print("Database initialized.")

def get_db_connection():
    conn = sqlite3.connect('task_manager.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_tasks(filters=None):
    try:
        conn = get_db_connection()
        query = 'SELECT * FROM tasks'
        params = []
        if filters:
            conditions = []
            if filters.get('priority'):
                placeholders = ','.join(['?'] * len(filters['priority']))
                conditions.append(f'priority IN ({placeholders})')
                params.extend(filters['priority'])
            if filters.get('status'):
                if filters['status'] == 'started':
                    conditions.append('start_time IS NOT NULL')
                elif filters['status'] == 'not_started':
                    conditions.append('start_time IS NULL')
            if filters.get('search'):
                conditions.append('description LIKE ?')
                params.append(f'%{filters["search"]}%')
            if not filters.get('show_completed', True):
                conditions.append('is_completed = 0')
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY created_at DESC'
        tasks = conn.execute(query, params).fetchall()
        conn.close()
        return tasks
    except Exception as e:
        print(f"Error getting tasks: {str(e)}")
        return []

def get_task_stats(filters=None):
    try:
        conn = get_db_connection()
        query = 'SELECT * FROM tasks'
        params = []
        if filters:
            conditions = []
            if filters.get('priority'):
                placeholders = ','.join(['?'] * len(filters['priority']))
                conditions.append(f'priority IN ({placeholders})')
                params.extend(filters['priority'])
            if filters.get('status'):
                if filters['status'] == 'started':
                    conditions.append('start_time IS NOT NULL')
                elif filters['status'] == 'not_started':
                    conditions.append('start_time IS NULL')
            if filters.get('search'):
                conditions.append('description LIKE ?')
                params.append(f'%{filters["search"]}%')
            if not filters.get('show_completed', True):
                conditions.append('is_completed = 0')
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        tasks = conn.execute(query, params).fetchall()
        conn.close()
        stats = {
            'total': len(tasks),
            'started': sum(1 for task in tasks if task['start_time']),
            'not_started': sum(1 for task in tasks if not task['start_time']),
            'by_priority': {
                'High': sum(1 for task in tasks if task['priority'] == 'High'),
                'Medium': sum(1 for task in tasks if task['priority'] == 'Medium'),
                'Low': sum(1 for task in tasks if task['priority'] == 'Low')
            }
        }
        return stats
    except Exception as e:
        print(f"Error getting stats: {str(e)}")
        return {'total': 0, 'started': 0, 'not_started': 0, 'by_priority': {'High': 0, 'Medium': 0, 'Low': 0}}

@app.route('/')
def index():
    try:
        filters = {
            'priority': request.args.getlist('priority'),
            'status': request.args.get('status'),
            'search': request.args.get('search'),
            'show_completed': request.args.get('show_completed', 'true').lower() == 'true'
        }
        tasks = get_tasks(filters)
        stats = get_task_stats(filters)
        return render_template('index.html', tasks=tasks, stats=stats, filters=filters)
    except Exception as e:
        flash(f'Error loading page: {str(e)}', 'danger')
        return render_template('index.html', tasks=[], stats={'total': 0, 'started': 0, 'not_started': 0, 'by_priority': {'High': 0, 'Medium': 0, 'Low': 0}}, filters={})

@app.route('/add_task', methods=['POST'])
def add_task():
    try:
        description = request.form.get('description', '').strip()
        if not description:
            flash('Task description is required', 'danger')
            return redirect(url_for('index'))

        priority = request.form.get('priority', 'Medium')
        due_date = request.form.get('due_date')
        notes = request.form.get('notes', '').strip()
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO tasks (description, priority, status, due_date, notes, progress) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (description, priority, 'not_started', due_date, notes, 0))
        conn.commit()
        conn.close()
        
        flash('Task added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding task: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    try:
        action = request.form.get('action')
        if not action:
            flash('No action specified', 'danger')
            return redirect(url_for('index'))

        conn = get_db_connection()
        if action == 'start':
            conn.execute('UPDATE tasks SET start_time = CURRENT_TIMESTAMP WHERE id = ?', (task_id,))
        elif action == 'stop':
            conn.execute('UPDATE tasks SET start_time = NULL, elapsed_time = 0 WHERE id = ?', (task_id,))
        elif action == 'complete':
            conn.execute('UPDATE tasks SET is_completed = 1, progress = 100 WHERE id = ?', (task_id,))
        
        conn.commit()
        conn.close()
        flash('Task updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating task: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/get_active_timer')
def get_active_timer():
    try:
        conn = get_db_connection()
        active_task = conn.execute('''
            SELECT id, start_time 
            FROM tasks 
            WHERE start_time IS NOT NULL AND is_completed = 0
        ''').fetchone()
        conn.close()
        
        if active_task and active_task['start_time']:
            try:
                start_time = datetime.fromisoformat(active_task['start_time'])
                elapsed = int((datetime.now() - start_time).total_seconds())
                return jsonify({'task_id': active_task['id'], 'elapsed': elapsed})
            except ValueError:
                return jsonify({'task_id': None, 'elapsed': 0})
        return jsonify({'task_id': None, 'elapsed': 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 