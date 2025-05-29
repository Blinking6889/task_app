import apiUtil
from flask import jsonify

def add_tasks_new(obj):
    if obj.location == None:
        return({"id": obj.id,
                    "description": obj.description,
                    "completed": obj.completed,
                    "due_date": obj.due_date})
    else:
        weather = apiUtil.get_weather_status(obj.location)
        return({"id": obj.id,
                    "description": obj.description,
                    "completed": obj.completed,
                    "due_date": obj.due_date,
                    "location": obj.location,
                    "weather": weather})

def bool_cleaner(bool_data):
    if isinstance(bool_data, bool):
        return bool_data
    elif isinstance(bool_data, str):
        if bool_data.lower() == 'true':
            return True
        elif bool_data.lower() == 'false':
            return False
        else:
            return jsonify({"error": "Invalid value for 'completed'. Must be true or false."}), 400