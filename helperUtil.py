from flask import jsonify

#Util Functions
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
        
