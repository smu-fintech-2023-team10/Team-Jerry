import uuid
from flask import Blueprint, request, jsonify
from firebase_admin import credentials, db
import requests
import json

userAPI = Blueprint('userAPI', __name__)


def get_auth_token_from_firebase():
    try:
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        auth_token = root_ref.child('auth_token')

        # Retrieve the user data
        auth_token_data = auth_token.get()

        return auth_token_data
    except Exception as e:
        return f"An Error occurred: {e}"


@userAPI.route('/add', methods=['POST'])
def create():
    try:
        data = request.json  # Get the JSON data from the request body

        id_value = data.get('id')  # Get the id_value from the JSON data, ID value is phone number as it is unique

        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Create a new child node with the provided id_value as the key
        user_ref = root_ref.child('user').child(id_value)
        user_ref.set(data)  # Use the parsed JSON data

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error occurred: {e}"
    
@userAPI.route('/lastTokenRefreshTime', methods=['GET'])
def get_token_refresh_time():
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        last_refresh_time = root_ref.child('auth_token').child('time').get()
        token = root_ref.child('auth_token').child('token').get()
        print(token)
        print(last_refresh_time)
        return {"lastRefreshDateTime:":last_refresh_time, "oldAuthToken":token}


@userAPI.route('/read/<user_id>', methods=['GET'])
def read(user_id):
    try:
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        user_ref = root_ref.child('user').child(user_id)

        # Retrieve the user data
        user_data = user_ref.get()

        if user_data:
            return jsonify(user_data), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return f"An Error occurred: {e}"

@userAPI.route('/update/<user_id>', methods=['PUT'])
def update(user_id):
    try:
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        user_ref = root_ref.child('user').child(user_id)

        # Update the user data with the new data from the request
        user_ref.update(request.json)

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error occurred: {e}"

@userAPI.route('/delete/<user_id>', methods=['DELETE'])
def delete(user_id):
    try:
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        user_ref = root_ref.child('user').child(user_id)

        # Delete the user node
        user_ref.delete()

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error occurred: {e}"