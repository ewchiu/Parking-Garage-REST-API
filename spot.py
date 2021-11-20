from flask import Blueprint, request, jsonify, Response
from google.cloud import datastore

client = datastore.Client()

bp = Blueprint('spot', __name__, url_prefix='/spots')