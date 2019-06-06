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

def makeQuery(id, query,params):
	userQuery = {"query": "query{"+query+"(id:"+id+")" + params +" }"}
	rest = (requests.post('http://35.232.95.82:5000/graphql',json= userQuery)).text
	serverResponse = json.loads(rest)
	user = serverResponse["data"][query]
	return user

@app.route('/test')
def testquery():
	id = "\""+ "b8aa227c-eaaf-479c-b89a-c33d4c536790"+"\""
	query = "postById"
	params = "{id createdAt idCreator content}"
	user = makeQuery(id, query, params)
	return dumps(user)
	
@app.route('/notifications')
def allNotif():
	_items = db.notifications.find()
	items = [item for item in _items]
	return dumps(items)

@app.route('/users/<user_id>/followers/<follower_id>', methods=['POST'])
def new_follow(user_id,follower_id):
	id = "{id:\"" + follower_id + "\""
	follower = makeQuery(follower_id, "userById","{id name last_name email}")
	item_doc = {
		'notificated_user': user_id,
		'follower_id' : follower[id],
		'follower_name': follower["name"] + " " + follower["last_name"],
		'date' : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
		'type' : "follow"}
	db.notifications.insert_one(item_doc)
	return dumps(item_doc)

@app.route('/posts/<post_id>/shares/<follower_id>', methods=['POST'])
def new_share(post_id,follower_id):
	id = "\""+post_id+"\""
	userQuery = {"query": "query{ postById(id:"+id+"){ idCreator } }"}
	rest = requests.post('http://35.232.95.82:5000/graphql',json= userQuery)
	serverResponse = rest.text
	user_id = serverResponse[34:-4]
	userreq = "\""+follower_id+"\""
	userQuery1 = {"query": "query{ userById(id:{id:"+userreq+"}){name} }"}
	rest1 = requests.post('http://35.232.95.82:5000/graphql',json= userQuery1)
	serverResponse1 = rest1.text
	user = serverResponse1[29:-4]
	app.logger.info(user)
	item_doc = {
		'notificated_user': user_id,
		'post_id' : post_id,
		'follower': user,
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
