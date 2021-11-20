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

