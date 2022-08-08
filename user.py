from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user
from GUID import GUID
import uuid

import os,sys

import logging
 
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/users' #dynamically retrieves db url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #off as modifications require extra memory and is not necessary in this case
 
db = SQLAlchemy(app) #initialization of connection, stored in variable db
login = LoginManager() #init of flask-login manager
login.init_app(app)
login.login_view = 'login'
CORS(app)

class Users(db.Model, UserMixin):
    __tablename__ = 'users'


    user_id = db.Column(GUID(), primary_key = True, default=uuid.uuid4) #uuid, char(32) in mysql
    first_name = db.Column(db.String(120), nullable = False)
    last_name = db.Column(db.String(120), nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password_hash = db.Column(db.String())    
    time_created = db.Column(db.DateTime(), nullable=False)
    last_updated = db.Column(db.DateTime(), nullable = False)


 
    def __init__(self, first_name, last_name, email, time_created, last_updated): #constructor. initializes record
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.time_created = time_created
        self.last_updated = last_updated
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password) #inbuilt from werkzeug security

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) #inbuilt from werkzeug security
 
    def json(self): #returns json representation of the table in dict form
        return {"user_id": self.user_id, "first_name": self.first_name, "last_name": self.last_name, "email": self.email, "time_created": self.time_created, "last_updated":self.last_updated} 

    def get_id(self):
        return str(self.user_id)



@login.user_loader
def load_user(user_id):
    return Users.query.get(user_id) #usermixin will convert int user_id to str



@app.route("/get_all_users") #get all users
def get_all():
    users = Users.query.all() #SQLAlchemy magic
    if len(users):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "users": [user.json() for user in users] #returns list of users in json format
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no users."
        }
    ), 404 #if status code is not specified, 200 OK is returned by default -- hence error 404 code is needed.


@app.route("/get_user/<string:email>")
def get_user_by_email(email):
    user = Users.query.filter_by(email=email).first() #returns a list of 1 item, .first() gets the first item. similar to limit 1 in sql
    if user:
        return jsonify(
            {
                "code": 200,
                "data": user.json()
            }
        )

    return jsonify(
        {
            "code": 404,
            "message": f"No user with {email} not found"
        }
    ), 404

@app.route("/for_login/<string:email>") #for login purposes, since it has to work with user object
def for_login(email):
    user = Users.query.filter_by(email=email).first() #returns a list of 1 item, .first() gets the first item. similar to limit 1 in sql
    if user != None:
        return user
    return jsonify(
        {
            "code": 404,
            "message": f"No user with {email} not found"
        }
    ), 404


def add_user(data): #create user
    data = request.get_json()
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    password = data['password']


    try:
        if Users.query.filter_by(email = email).first():
            return {
                
                    "code": 400,
                    "data": Users.query.filter_by(email = email).first().json(),
                    "message": "User account already exists for this email. Please log in instead"
                }


        user = Users(first_name = first_name, last_name = last_name, email = email, time_created = datetime.now(), last_updated = datetime.now()) #user_id auto generated
        user.set_password(password) #make use of hashing/salting funct via custom set_password funct defined in user class
        db.session.add(user)         #add user to user table
        db.session.commit()
        return {
                "code": 201,
                "data": user.json() #show user info added to db
            }
        

    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        ex_str = str(exc_obj) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
        print(ex_str)

        return {
                "code": 500,
                "data": {
                    "email": email
                },
                "message": "An error occurred while creating this user account."
            }



@app.route("/update_user", methods = ['PUT'])
def update_user():
    try:
        email = data['email']
        if (Users.query.filter_by(email = email).first()): #user found
                data = request.get_json() #gets json data from the body of the request
    
                to_update = Users.query.filter_by(email = email).first()
                if data['first_name']:
                    to_update.first_name = data['first_name']
                    to_update.last_updated = datetime.now()
                if data['last_name']:
                    to_update.last_name = data['last_name']
                    to_update.last_updated = datetime.now()
                if data['email']:
                    to_update.email = data['email']
                    to_update.last_updated = datetime.now()
                if data['password']:
                    to_update.password = data['password']
                    to_update.last_updated = datetime.now()

                db.session.commit()
                return jsonify( #user successfully updated
                    {
                        "code": 201,
                        "data": to_update.json()
                    }
                ), 201 
        else:
            return jsonify( #user not found
                {
                    "code": 404,
                    "message": f"User not found"
                }
            ), 404
    except:
        return jsonify( #error in updating
            {
                "code": 500,
                "data": {
                    "email" : email
                },
            "message": f"An error occured updating user information for user with email {email}"
            }
        ), 500




@app.route("/delete_user/<string:email>", methods=['DELETE'])
def delete_user(email):
    try:
        user = Users.query.filter_by(email=email).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": {
                        "email": email
                    },
                    "message": f"User {email} deleted"
                }
            )
        else:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "email": email
                    },
                    "message": f"User {email} not found"
                }
            ), 404
    except:
            return jsonify(
                {
                    "code": 500,
                    "data": {
                        "email": email
                    },
                    "message": f"An error occured when trying to delete user {email}"
                }
            ), 500



@app.route("/login", methods = ['POST', 'GET']) #retrieve user object, do comparison, render page
def login():
    try:
        if current_user.is_authenticated: #if authenticated, redirect to user home page 
            return "Authenticated"
        if request.method == 'POST': #if a new login req is made with post
            data = request.get_json()
            email = data['email']
            password = data['password']
            user = Users.query.filter_by(email = email).first()#get user object based off email since email is unique
            if user is not None and user.check_password(password): #if user is found and password is verified. check_password method
                login_user(user) #login user with login_user 
                return jsonify(
                {
                    "code": 200,
                    "data": {
                        "user": user.json()
                    },
                    "message": "Success"
                }
                ), 200 #redirect to home view
            else:
                return jsonify(
                {
                    "code": 400,
                    "data": {
                        "email": email
                    },
                    "message": "Error"
                }
                ), 400 #redirect to home view
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        ex_str = str(exc_obj) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
        print(ex_str)
        return jsonify(
        {
            "code": 500,
            "data": {
                "email": email
            },
            "message": "Error in logging in"
        }
        ), 500 



@app.route("/signup", methods = ['POST']) 
def signup():
    if current_user.is_authenticated: #logout and go to signout page? maybe they wanna make new account, need to look into this
        return "Authenticated"

    if request.method == 'POST': #posting new user to register
        data = request.get_json()
        signup_results = add_user(data)
        code = signup_results['code']

        if code == 201: #successful register
            return jsonify(
                {
                    "code": 201,
                    "data":signup_results['data']
                }
            ), 201
    
        elif code == 400:
            return jsonify(
                {
                    "code": 400,
                    "data": signup_results['data']
                }
            ), 400

 #if not already authenticated or if post req not made, essentially just getting the login page, so return signup view

@app.route("/logout")
def logout():
    logout_user()
    return jsonify(
        {
            "code": 200,
            "data":"Logout"
        }
    ), 200

app.secret_key = "fd08462624b345138cfd113014ce76bb"

if __name__ == '__main__':
    app.run(port=5002, debug=True)


