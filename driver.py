from flask import Blueprint, request, jsonify, Response, session
from google.cloud import datastore
from google.auth.transport import requests
from google.oauth2 import id_token

client = datastore.Client()
bp = Blueprint('driver', __name__, url_prefix='/drivers')

