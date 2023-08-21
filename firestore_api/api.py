import uuid
from flask import Blueprint, request, jsonify
from firebase_admin import credentials, db


userAPI = Blueprint('userAPI', __name__)

@userAPI.route('/add', methods=['POST'])
def create():
    try:
        id = uuid.uuid4()
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Create a new child node with the generated UUID as the key
        user_ref = root_ref.child('user').child(id.hex)
        user_ref.set(request.json)

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error occurred: {e}"

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