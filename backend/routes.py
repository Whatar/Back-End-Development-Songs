from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})
    return {"count": count}, 200

@app.route("/song", methods=["GET"])
def get_songs():
    """return all songs"""
    songs = list(db.songs.find())
    return jsonify(parse_json(songs)), 200


@app.route("/song/<id>", methods=["GET"])
def get_song_by_id(id):
    """return a single song"""
    song = db.songs.find_one({"id": int(id)})
    if song:
        return jsonify(parse_json(song)), 200
    else:
        return jsonify({"message": "song with id not found"}), 404


@app.route("/song", methods=["POST"])
def create_song():
    """create a new song"""
    song = request.get_json()
    if db.songs.find_one({"id": song["id"]}):
        return jsonify({"Message": "song with id {song['id']} already present"}), 302
    result = db.songs.insert_one(song)
    return jsonify({"inserted id": str(result.inserted_id)}), 201


@app.route("/song/<string:id>", methods=["PUT"])
def update_song(id):
    """Update a song"""
    song = request.get_json()
    song["id"] = int(id)
    original_song = db.songs.find_one({"id": int(id)})

    if not original_song:
        return jsonify({"message": "song not found"}), 404

    song["_id"] = original_song["_id"]
    result = db.songs.replace_one({"id": int(id)}, song)

    if result.modified_count == 0:
        return jsonify({"message": "song not updated"}), 400

    updated_song = db.songs.find_one({"id": int(id)})
    updated_song["_id"] = str(updated_song["_id"])  # Convert _id to string for JSON response
    return jsonify(updated_song), 200


@app.route("/song/<string:id>", methods=["DELETE"])
def delete_song(id):
    """Delete a song"""
    result = db.songs.delete_one({"id": int(id)})
    if result.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404
    return jsonify({"message": "Song deleted"}), 200
