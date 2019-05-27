import os 
import datetime 
import json
from flask import Flask, redirect, url_for, request, render_template,jsonify 
from pymongo import MongoClient
from bson.json_util import dumps
app= Flask(__name__)
client= MongoClient(os.environ['RAPUNZEL_DB_PORT_27017_TCP_ADDR'])
db= client.notifications 

@app.route('/notifications')
def todo():
	_items = db.notifications.find()
	items = [item for item in _items]
	return dumps(items)

@app.route('/users/<user_id>/followers/<follower_id>', methods=['POST'])
def new_follow(user_id,follower_id):
	item_doc = {
		'notificated_user': user_id,
		'follower': follower_id,
		'date' : datetime.datetime.now(),
		'type' : "follow"}
	db.notifications.insert_one(item_doc)
	return dumps(item_doc)

@app.route('/users/<user_id>/posts/<post_id>/shares/<follower_id>', methods=['POST'])
def new_share(user_id,post_id,follower_id):
    item_doc = {
        'notificated_user': user_id,
		'post_id' : post_id,
        'follower': follower_id,
        'date' : datetime.datetime.now(),
		'type' : "share"}
    db.notifications.insert_one(item_doc)
    return dumps(item_doc)

@app.route('/notifications/<user_id>')
def get_notifications(user_id):
    _items = db.notifications.find({"notificated_user": user_id})
    items = [item for item in _items]
    return dumps(items)

if __name__ == "__main__":
	app.run(host='0.0.0.0', port= '5050' , debug=True)
