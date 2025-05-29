from flask import Flask, jsonify, abort,request
from sqlalchemy import Column,create_engine,Integer,String,Select,Boolean, ForeignKey
from sqlalchemy.orm import declarative_base,sessionmaker,scoped_session, relationship
import json
import os


#LOCAL CLASSS IMPORTS
import helperUtil
import builders
import user_registration as credential_logic


#Define Database Structure
Base = declarative_base()
class Task(Base):
    __tablename__ = "task_data"
    id = Column(Integer, primary_key=True)
    description = Column(String)
    completed = Column(Boolean)
    due_date = Column(String)
    location = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=True)

#Initialize Database
#POSTGRES DB CONNECTION
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

#SQLITE DB CONNECTION
# engine = create_engine("sqlite+pysqlite:///tasks.db", echo=True, future=True)

Base.metadata.create_all(engine)

#Connect To Database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Validate database state. If does not exist, create DB.
with SessionLocal() as session:
    if session.query(Task).count() == 0:
        task_collection = []
        with open('sample_data.json') as f:
            json_data = json.load(f)
            for i in json_data:
                task = Task()
                task.id = i['id']
                task.description = i['description']
                task.completed = i['completed']
                task.due_date = i['due_date']
                task.location = i['location']
                task_collection.append(task)
                session.add_all(task_collection)
                session.commit()
                print("Database successfully Created")
            else:
                print("Database found. Loading existing data.")

#Start Flask App and Initialize Database Session
app = Flask(__name__)
db_conn = scoped_session(SessionLocal)

#API Implementation
#Placeholder Index
@app.route("/")
def index():
    return jsonify(f'Hello World!')

#User Registration Logic
@app.route("/register", methods=['post'])
def register_user():
    user_req = request.get_json()
    if user_req:
        user_query = Select(User).where(User.username == user_req['username'])
        check_existing = session.scalars(user_query).first()
        if check_existing:
            return jsonify(f'Username already exists.', 409)
        else:
            new_user = credential_logic.create_user(user_req)
            user = User()
            user.username = new_user[0]
            user.hashed_password = new_user[1]
            session.add(user)
            session.commit()
            return jsonify(f'User Created Successfully', 201)

#User Login Logic
@app.route("/login", methods=['post'])
def login_user():
    user_req = request.get_json()
    if not user_req or not user_req.get('username') or not user_req.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
    
    user_query = Select(User).where(User.username == user_req['username'])
    user_from_db = session.scalars(user_query).first() # Changed variable name for clarity

    if user_from_db and credential_logic.validate_credentials(user_req['password'], user_from_db.hashed_password):
        # If user exists and password is correct:
        # Create token using the user's INTEGER ID from the database
        token_response = credential_logic.create_access_token(user_from_db.id)
        return jsonify(token_response), 200   
    else:
        # User not found or password incorrect
        return jsonify({'message': 'Invalid credentials'}), 401 # 401 is more standard for bad login
            

#CRUD OPERATION LOGIC
#Define Tasks App Get Route
@app.route("/tasks")
@app.route("/tasks/")
@app.route("/tasks/<int:id>")
@credential_logic.validate_token
def displayTasks(current_userid, id=None):
    session = db_conn()
    if id == None:
        queryallusertasks = Select(Task).where(Task.owner_id == current_userid)
        allTasks = session.scalars(queryallusertasks).all()
        tasks_array = []
        for i in allTasks:
            tasks_array.append(builders.add_tasks_new(i))
        return jsonify(tasks_array)
    else:
        queryselectusertask = Select(Task).where(Task.owner_id == current_userid and Task.id == id)
        task = session.scalars(queryselectusertask).first()
        if task:
            return jsonify(builders.add_tasks_new(task))
        else:
            abort(404)

#POST METHOD
@app.route("/tasks/", methods=['post'])
@credential_logic.validate_token
def add_new_task(current_userid):
    session = db_conn()
    new_task = request.get_json()
    if new_task and 'location' in new_task:
        task = Task()
        task.id=int(new_task['id'])
        task.description=new_task['description']
        task.completed = helperUtil.bool_cleaner(new_task['completed'])
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
        task.completed = helperUtil.bool_cleaner(new_task['completed'])
        task.due_date=new_task['due_date']
        task.location=None
        task.owner_id = current_userid
        session.add(task)
        session.commit()
        return 'POST CREATED', 201
    else:
        abort(404)

#UPDATE METHOD
@app.route("/tasks/<int:id>", methods=['put'])
@credential_logic.validate_token
def update_task(current_userid,id):
    session = db_conn()
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
@app.route("/tasks/<int:id>", methods=['delete'])
@credential_logic.validate_token
def delet_task(current_userid,id):
    db_conn = scoped_session(SessionLocal)
    session = db_conn()
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

if __name__ == "__main__":
    app.run(debug=True)
