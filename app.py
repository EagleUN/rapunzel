import os 
import datetime 
import json
import logging
import requests 
from flask import Flask, redirect, url_for, request, render_template,jsonify 
from pymongo import MongoClient
from bson.json_util import dumps
from graphqlclient import GraphQLClient
app= Flask(__name__)
client= MongoClient(host=['rapunzel_db:27017'], connect = True)
db= client.notifications 
QLclient = GraphQLClient('http://35.232.95.82:5000/graphql')

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

@app.route('/notifications')
def allNotif():
	_items = db.notifications.find()
	items = [item for item in _items]
	return dumps(items)

@app.route('/users/<user_id>/followers/<follower_id>', methods=['POST'])
def new_follow(user_id,follower_id):
	item_doc = {
		'notificated_user': user_id,
		'follower': follower_id,
		'date' : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
		'type' : "follow"}
	db.notifications.insert_one(item_doc)
	return dumps(item_doc)

@app.route('/posts/<post_id>/shares/<follower_id>', methods=['POST'])
def new_share(post_id,follower_id):
	item_doc = {
		'notificated_user': "1daba304-fa24-402c-bee6-8d4860374aed",
		'post_id' : post_id,
		'follower': follower_id,
		'date' : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
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
