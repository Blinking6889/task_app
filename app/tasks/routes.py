from flask import Blueprint, request, jsonify, abort
from sqlalchemy import Select

from app import db_session
from app.models import Task
from app.auth.services import validate_token
from .services import add_tasks_new, bool_cleaner
tasks_bp = Blueprint('tasks_bp', __name__, url_prefix='/tasks')

#CRUD OPERATION LOGIC
#Define Tasks App Get Route
@tasks_bp.route("/")
@tasks_bp.route("/tasks/")
@tasks_bp.route("/<int:id>")
@validate_token
def displayTasks(current_userid, id=None):
    session = db_session()
    if id == None:
        queryallusertasks = Select(Task).where(Task.owner_id == current_userid)
        allTasks = session.scalars(queryallusertasks).all()
        tasks_array = []
        for i in allTasks:
            tasks_array.append(add_tasks_new(i))
        return jsonify(tasks_array)
    else:
        queryselectusertask = Select(Task).where(Task.owner_id == current_userid and Task.id == id)
        task = session.scalars(queryselectusertask).first()
        if task:
            return jsonify(add_tasks_new(task))
        else:
            abort(404)

#POST METHOD
@tasks_bp.route("/tasks/", methods=['post'])
@validate_token
def add_new_task(current_userid):
    session = db_session()
    new_task = request.get_json()
    if new_task and 'location' in new_task:
        task = Task()
        task.id=int(new_task['id'])
        task.description=new_task['description']
        task.completed = bool_cleaner(new_task['completed'])
        task.due_date=new_task['due_date']
        task.location=new_task['location']
        task.owner_id = current_userid
        session.add(task)
        session.commit()
        return 'POST CREATED', 201
    elif new_task:
        task = Task()
        task.id=int(new_task['id'])
        task.description=new_task['description']
        task.completed = bool_cleaner(new_task['completed'])
        task.due_date=new_task['due_date']
        task.location=None
        task.owner_id = current_userid
        session.add(task)
        session.commit()
        return 'POST CREATED', 201
    else:
        abort(404)

#UPDATE METHOD
@tasks_bp.route("/tasks/<int:id>", methods=['put'])
@validate_token
def update_task(current_userid,id):
    session = db_session()
    new_task = request.get_json()
    if new_task:
        task = session.get(Task, id)
        if task:
            if 'description' in new_task and new_task['description'] != task.description:
                task.description = new_task['description']
            if 'completed' in new_task:
                base_completed = new_task['completed']
                if isinstance(base_completed, bool) and base_completed != task.completed:
                    task.completed = base_completed
                elif isinstance(base_completed, str):
                    if base_completed.lower() == 'true' and not task.completed:
                        task.completed = True
                        print("Converted Completed From String")
                    elif base_completed.lower() == 'false' and task.completed:
                        task.completed = False
                        print("Converted Completed From String")
                    else:
                        return jsonify({"error": "Invalid value for 'completed'. Must be true or false."}), 400
            if 'due_date' in new_task and new_task['due_date'] != task.due_date:
                task.due_date = new_task['due_date']
            if 'location' in new_task and new_task['location'] != task.location:
                task.location = new_task['location']
            session.commit()
            return jsonify({"id": task.id,
                            "description": task.description,
                            "completed": task.completed,
                            "due_date": task.due_date})             
        else:
            abort(404)

#DELETE METHOD
@tasks_bp.route("/tasks/<int:id>", methods=['delete'])
@validate_token
def delet_task(current_userid,id):
    # db_conn = scoped_session(SessionLocal)
    session = db_session()
    new_task = request.get_json()
    if new_task == None:
        abort(404)
    if new_task:
        db_obj = session.get(Task, id)
        if db_obj:
            session.delete(db_obj)
            session.commit()
            return 'No Content', 204
    else:
        abort(404)