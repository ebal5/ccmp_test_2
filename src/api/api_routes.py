from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
import json
from typing import Dict, Any, Optional

from ..models.base import get_db
from ..models import Task, Project, TimeEntry, ApiKey, TaskStatus
from ..controllers import TaskController, ProjectController, TimeEntryController, NotificationController

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize controllers
task_controller = TaskController()
project_controller = ProjectController()
time_entry_controller = TimeEntryController()
notification_controller = NotificationController()

# API key authentication
def authenticate_api_key(api_key: str, db: Session) -> bool:
    """Authenticate an API key"""
    key = db.query(ApiKey).filter(
        ApiKey.key == api_key,
        ApiKey.is_active == True
    ).first()
    
    if key:
        # Update last used timestamp
        key.last_used_at = datetime.utcnow()
        db.add(key)
        db.commit()
        return True
        
    return False

@api_bp.before_request
def verify_api_key():
    """Verify API key for all API routes"""
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        return None
        
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({"error": "API key required"}), 401
        
    db = next(get_db())
    if not authenticate_api_key(api_key, db):
        return jsonify({"error": "Invalid API key"}), 401

# Task routes
@api_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    db = next(get_db())
    tasks = task_controller.get_all(db)
    return jsonify([{
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "estimated_time": task.estimated_time,
        "buffer_time": task.buffer_time,
        "actual_time": task.actual_time,
        "completion_percentage": task.completion_percentage,
        "project_id": task.project_id,
        "is_critical_chain": task.is_critical_chain
    } for task in tasks])

@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id: int):
    """Get a specific task"""
    db = next(get_db())
    task = task_controller.get(db, task_id)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    return jsonify({
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "estimated_time": task.estimated_time,
        "buffer_time": task.buffer_time,
        "actual_time": task.actual_time,
        "completion_percentage": task.completion_percentage,
        "project_id": task.project_id,
        "is_critical_chain": task.is_critical_chain,
        "start_date": task.start_date.isoformat() if task.start_date else None,
        "end_date": task.end_date.isoformat() if task.end_date else None,
        "due_date": task.due_date.isoformat() if task.due_date else None
    })

@api_bp.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id: int):
    """Start a task"""
    db = next(get_db())
    task = task_controller.start_task(db, task_id)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    # Start time tracking
    time_entry = time_entry_controller.start_timer(db, task_id=task_id)
    
    return jsonify({
        "message": f"Task '{task.name}' started",
        "task_id": task.id,
        "status": task.status,
        "time_entry_id": time_entry.id
    })

@api_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id: int):
    """Complete a task"""
    db = next(get_db())
    
    # Stop any active time entries for this task
    active_entries = db.query(TimeEntry).filter(
        TimeEntry.task_id == task_id,
        TimeEntry.end_time == None
    ).all()
    
    for entry in active_entries:
        time_entry_controller.stop_timer(db, entry.id)
    
    # Mark task as complete
    task = task_controller.complete_task(db, task_id)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    return jsonify({
        "message": f"Task '{task.name}' completed",
        "task_id": task.id,
        "status": task.status,
        "actual_time": task.actual_time
    })

@api_bp.route('/tasks/<int:task_id>/progress', methods=['POST'])
def update_task_progress(task_id: int):
    """Update task progress"""
    data = request.json
    if not data or 'completion_percentage' not in data:
        return jsonify({"error": "completion_percentage is required"}), 400
        
    completion_percentage = float(data['completion_percentage'])
    
    db = next(get_db())
    task = task_controller.update_progress(db, task_id, completion_percentage)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    return jsonify({
        "message": f"Task '{task.name}' progress updated",
        "task_id": task.id,
        "completion_percentage": task.completion_percentage
    })

# Time tracking routes
@api_bp.route('/time/start', methods=['POST'])
def start_timer():
    """Start a timer"""
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400
        
    task_id = data.get('task_id')
    category = data.get('category')
    
    if not task_id and not category:
        return jsonify({"error": "Either task_id or category is required"}), 400
        
    db = next(get_db())
    time_entry = time_entry_controller.start_timer(db, task_id=task_id, category=category)
    
    return jsonify({
        "message": "Timer started",
        "time_entry_id": time_entry.id,
        "start_time": time_entry.start_time.isoformat()
    })

@api_bp.route('/time/<int:time_entry_id>/stop', methods=['POST'])
def stop_timer(time_entry_id: int):
    """Stop a timer"""
    db = next(get_db())
    time_entry = time_entry_controller.stop_timer(db, time_entry_id)
    
    if not time_entry:
        return jsonify({"error": "Time entry not found"}), 404
        
    return jsonify({
        "message": "Timer stopped",
        "time_entry_id": time_entry.id,
        "duration": time_entry.duration,
        "task_id": time_entry.task_id
    })

# Project routes
@api_bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    db = next(get_db())
    projects = project_controller.get_all(db)
    return jsonify([{
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "buffer_status": project.buffer_status,
        "buffer_consumption": project.buffer_consumption,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "target_end_date": project.target_end_date.isoformat() if project.target_end_date else None
    } for project in projects])

@api_bp.route('/projects/<int:project_id>/buffer', methods=['GET'])
def get_project_buffer(project_id: int):
    """Get project buffer information"""
    db = next(get_db())
    project = project_controller.get(db, project_id)
    
    if not project:
        return jsonify({"error": "Project not found"}), 404
        
    # Calculate current buffer consumption
    buffer_consumption = project_controller.calculate_project_buffer_consumption(db, project_id)
    
    return jsonify({
        "project_id": project.id,
        "project_name": project.name,
        "buffer_size": project.project_buffer,
        "buffer_consumption": project.buffer_consumption,
        "buffer_status": project.buffer_status
    })