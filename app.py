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

@app.route('/test')
def testquery():
	id = "77bd2e0f-50fe-4c58-9800-1db11035ef64"
	id = "\""+id+"\""
	userQuery = {"query": "query{ userById(id:{id:"+id+"}){name} }"}
	rest = requests.post('http://35.232.95.82:5000/graphql',json= userQuery)
	serverResponse = rest.text
	user = serverResponse[29:-4]
	return user
	
@app.route('/notifications')
def allNotif():
	_items = db.notifications.find()
	items = [item for item in _items]
	return dumps(items)

@app.route('/users/<user_id>/followers/<follower_id>', methods=['POST'])
def new_follow(user_id,follower_id):
	id = "\""+follower_id+"\""
	userQuery = {"query": "query{ userById(id:{id:"+id+"}){name} }"}
	rest = requests.post('http://35.232.95.82:5000/graphql',json= userQuery)
	serverResponse = rest.text
	user = serverResponse[29:-4]
	item_doc = {
		'notificated_user': user_id,
		'follower': user,
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
