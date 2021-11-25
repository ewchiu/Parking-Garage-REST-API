from flask import Blueprint, request, jsonify, make_response
from google.cloud import datastore
from jwt_ops import verify

client = datastore.Client()
bp = Blueprint('user', __name__, url_prefix='/users')

# get all users
@bp.route('', methods=['GET'])
def get_users():
	if request.method == 'GET':

		if 'application/json' not in request.accept_mimetypes:
			error = {"Error": "Not Acceptable"}
			return jsonify(error), 406
			
		query = client.query(kind='users')
		results = list(query.fetch())

		for user in results:
			user['id'] = user.key.id

		return jsonify(results), 200

	else:
		res = make_response({"Error": "Method not recognized"})
		res.headers.set('Allow', ['GET'])
		res.status_code = 405
		return res
