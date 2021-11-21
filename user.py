from flask import Blueprint, request, jsonify, Response, session
from google.cloud import datastore
from google.auth.transport import requests
from google.oauth2 import id_token

client = datastore.Client()
bp = Blueprint('user', __name__, url_prefix='/users')

# get all users
@bp.route('', methods=['GET'])
def get_users():
    if request.method == 'GET':
        query = client.query(kind='users')
        results = list(query.fetch())

        for user in results:
            user['id'] = user.key.id
            user['self'] = f'{request.url}/{user.key.id}'

        return jsonify(results), 200

    else:
        return 'Method not recognized'

# get user by id
@bp.route('/<user_id>', methods=['GET'])
def get_user_by_id(user_id):

    if request.method == 'GET':
        sub = JWT_verify()

        if sub is False:
            return jsonify({'Error': 'JWT could not be verified'}), 401
        elif sub is None:
            return jsonify({'Error': 'No JWT was provided'}), 401
        elif sub != user_id:
            return jsonify({'Error': 'You do not have access to this user info.'}), 401

        user_key = client.key('users', int(user_id))
        user = client.get(key=user_key)

        if not user:
            error = {"Error": "No user with this user_id exists"}
            return jsonify(error), 404

        user['id'] = user.key.id
        user['self'] = f'{request.url}/{user.key.id}'
        return jsonify(user), 200

def JWT_verify():
    req = requests.Request()
    jwt = request.headers.get('Authorization')

    if jwt:
        req = requests.Request()
        jwt = jwt.split(" ")[1]

        try:
            sub = id_token.verify_oauth2_token(jwt, req, session['credentials']['client_id'])
            sub = sub['sub']
        except:
            return False

    else:
        return None
    
    return sub
