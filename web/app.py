from flask import Flask, request, jsonify
from flask_restful import Api, Resource
import os
import bcrypt

from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")  # making connection to db
db = client.SentencesDatabase  # creating new db
users = db["Users"]  # creating a collection called users to store user/pwd


def verify_password(username, password):
    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]
    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    return False


def count_tokens(username):
    tokens = users.find({
        "Username": username
    })[0]["Tokens"]
    return tokens


class Register(Resource):
    def post(self):
        # get the posted data by user
        posted_data = request.get_json()

        # got the data
        username = posted_data["username"]
        password = posted_data["password"]

        # to encrypt the password
        # hash(123 + salt) = Ssadjakfn
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        # store username and password in SentencesDatabase
        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Sentence": "",
            "Tokens": 6
        })
        response = {
            "StatusCode": 200,
            "Message": "You have successfully signed up for the API"
        }
        return jsonify(response)


class Store(Resource):
    def post(self):
        # Step1 Get the posted data
        posted_data = request.get_json()

        # Step2 read the data from the request
        username = posted_data["username"]
        password = posted_data["password"]
        sentence = posted_data["sentence"]

        # Step3 Verify the username and password match
        correct_pwd = verify_password(username, password)

        if not correct_pwd:
            response = {
                "StatusCode": 302,
                "Message": "Invalid user or password"
            }
            return jsonify(response)

        # Step4 Verify if user has enough tokens
        num_tokens = count_tokens(username)
        if num_tokens <= 0:
            response = {
                "StatusCode": 301,
                "Message": "Not enough tokens"
            }
            return jsonify(response)

        # Step5 Store the sentence and take one token away and return 200
        users.update_one({
            "Username": username
         },
         {"$set": {
                "Sentence": sentence,
                "Tokens": num_tokens - 1
         }
        })
        response = {
            "StatusCode": 200,
            "Message": "Sentence saved successfully"
        }
        return jsonify(response)


class Get(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]

        # check valid user
        valid_user = verify_password(username, password)

        if not valid_user:
            response = {
                "StatusCode": 302,
                "Message": "Invalid user or password"
            }
            return jsonify(response)

        num_tokens = count_tokens(username)
        if num_tokens <= 0:
            response = {
                "StatusCode": 301,
                "Message": "Not enough tokens"
            }
            return jsonify(response)

        # Make the user pay
        users.update_one({
            "Username": username
        },
            {"$set": {
                "Tokens": num_tokens - 1
            }
            })

        retrieved_sentence = users.find({
            "Username": username
        })[0]["Sentence"]
        response = {
            "StatusCode": 200,
            "Sentence": retrieved_sentence
        }
        return jsonify(response)


api.add_resource(Register, '/register')
api.add_resource(Store, '/store')
api.add_resource(Get, '/get')

if __name__=="__main__":
    app.run(host='0.0.0.0')