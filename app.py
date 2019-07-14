import os 
import datetime 
import json
import logging
import requests 
from flask import Flask, redirect, url_for, request, render_template,jsonify 
from pymongo import MongoClient
from bson.json_util import dumps
from firebase_admin import messaging
from firebase_admin import credentials
import firebase_admin

# Initialize firebase
# cred = credentials.Certificate("~/firebase-adminsdk-secret-key.json")
firebase_admin.initialize_app()

app= Flask(__name__)
client= MongoClient(host=['rapunzel-db:27017'], connect = True)
db= client.notifications 

def buildNotification(title, body, token):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        android=messaging.AndroidConfig(
            ttl=datetime.timedelta(seconds=3600),
            priority='normal',
            notification=messaging.AndroidNotification(
                icon='stock_ticker_update',
                color='#f45342'
            ),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(badge=42),
            ),
        ),
	token=token
    )
    return message

def sendNotification(title, body, cursor):
	for doc in cursor:
		app.logger.info("doc: " + str(doc))
		tokens = doc["tokens"]
		app.logger.info("Tokens: " + str(tokens))
		for token in tokens:
			app.logger.info("Token: " + str(token))
			message = buildNotification(title, body, token)
			try:
				response = messaging.send(message)
				print('Sent notification and got response:', response)
			except:
				pass

def makeQuery(id, query,params):
	userQuery = {"query": "query{"+query+"(id:"+id+")" + params +" }"}
	rest = (requests.post('http://walt:5000/graphql',json= userQuery)).text
	serverResponse = json.loads(rest)
	app.logger.info(rest)
	data = serverResponse["data"][query]
	return data

@app.route('/test')
def testquery():
	user_id = "777c3dc5-e33c-497a-ab09-a93a38516b6c"
	_items = db.notifications.find({"notificated_user": user_id})
	items = [item for item in _items]
	for i in items: 
		follower_id = i["follower"]
		follower = makeQuery("{id:\""+follower_id+ "\"}", "userById","{id name last_name email}")
		if i["type"] == "follow":
			i["follower_name"] = follower["name"] + " " + follower["last_name"]
		else: 
			post_id = i["post_id"]
			post = makeQuery("\""+post_id+"\"","postById","{id createdAt idCreator content}")
			i["content"] = post["content"]
			i["follower_name"] = follower["name"] + " " + follower["last_name"]
	return dumps(items)
	
@app.route('/notifications')
def allNotif():
	_items = db.notifications.find()
	items = [item for item in _items]
	for i in items: 
		follower_id = i["follower"]
		follower = makeQuery("{id:\""+follower_id+ "\"}", "userById","{id name last_name email}")
		i["follower_name"] = follower["name"] + " " + follower["last_name"]
		if i["type"] == "share":
			post_id = i["post_id"]
			post = makeQuery("\""+post_id+"\"","postById","{id createdAt idCreator content}")
			i["content"] = post["content"]
	return dumps(items)

@app.route('/users/<user_id>/tokens/<token>', methods=['POST'])
def new_token(user_id,token):
	query = {'user_id': user_id}
	_found = client.notifications.user_tokens.find(query)
	found = [ item for item in _found ]
	if len(found) > 0:
		found = found[0]
		if (token in found["tokens"]) == False:
			found["tokens"].append(token)
			if len(found["tokens"]) > 5:
				found["tokens"] = found["tokens"][1:]
		app.logger.info("New token added:")
		app.logger.info(found)
		client.notifications.user_tokens.update_one(query, {"$set": found})
		return dumps(found)
	else:
		app.logger.info("Not a new token :C")
		item_doc = {
			'user_id': user_id,
			'tokens' : [token]
		}
		client.notifications.user_tokens.insert_one(item_doc)
		app.logger.info("New token:")
		app.logger.info(item_doc)
		return dumps(item_doc)

@app.route('/users/<user_id>/followers/<follower_id>', methods=['POST'])
def new_follow(user_id,follower_id):
	id = "{id:\""+ follower_id + "\"}"
	follower = makeQuery("{id:\""+follower_id+ "\"}", "userById","{id name last_name email}")
	item_doc = {
		'notificated_user': user_id,
		'follower' : follower_id,
		'date' : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
		'type' : "follow"}
	db.notifications.insert_one(item_doc)

	tokens = client.notifications.user_tokens.find({"user_id": user_id})
	follower = makeQuery("{id:\""+follower_id+ "\"}", "userById","{id name last_name email}")
	followerName = follower["name"] + " " + follower["last_name"]
	notificationTitle = "You have a new follower"
	notificationBody = followerName + " is now following you"
	sendNotification(notificationTitle, notificationBody, tokens)

	return dumps(item_doc)

@app.route('/posts/<post_id>/shares/<follower_id>', methods=['POST'])
def new_share(post_id,follower_id):
	post = makeQuery("\""+post_id+"\"","postById","{id createdAt idCreator content}")
	notificated_user = post["idCreator"]
	id = "{id:\""+follower_id+ "\"}"
	follower = makeQuery(id,"userById","{id name last_name email}")
	#app.logger.info(user)
	item_doc = {
		'notificated_user': notificated_user,
		'post_id' : post_id,
		'follower': follower_id,
		'date' : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
		'type' : "share"}
	db.notifications.insert_one(item_doc)

	tokens = client.notifications.user_tokens.find({"user_id": notificated_user})
	follower = makeQuery("{id:\""+follower_id+ "\"}", "userById","{id name last_name email}")
	followerName = follower["name"] + " " + follower["last_name"]
	notificationTitle = "Your post was shared"
	notificationBody = followerName + " has shared your post"
	sendNotification(notificationTitle, notificationBody, tokens)

	return dumps(item_doc)

@app.route('/notifications/<user_id>')
def get_notifications(user_id):
	_items = db.notifications.find({"notificated_user": user_id})
	items = [item for item in _items]
	for i in items: 
		follower_id = i["follower"]
		follower = makeQuery("{id:\""+follower_id+ "\"}", "userById","{id name last_name email}")
		i["follower_name"] = follower["name"] + " " + follower["last_name"]
		if i["type"] == "share":
			post_id = i["post_id"]
			post = makeQuery("\""+post_id+"\"","postById","{id createdAt idCreator content}")
			i["content"] = post["content"]
	return dumps(items)

if __name__ == "__main__":
	print("Starting rapunzel")
	app.run(host='0.0.0.0', port= '5050' , debug=True)

