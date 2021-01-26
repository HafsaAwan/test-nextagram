from models.user import User
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token

sessions_api_blueprint = Blueprint('sessions_api',
                             __name__,
                             template_folder='templates')

@sessions_api_blueprint.route('/', methods=['POST'])
def create():
    params = request.json
    user = User.get_or_none(User.email == params.get("email"))
    if user and check_password_hash(user.password_hash, params.get("password")):
        token = create_access_token(identity=user.id)
        return jsonify({"token": token})
    else:
        return jsonify("Bad login")
