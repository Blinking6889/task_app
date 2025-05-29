import apiUtil

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

