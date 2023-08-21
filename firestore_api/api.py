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
