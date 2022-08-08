from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from GUID import GUID
import logging
from flask_cors import CORS
import uuid
import os,sys

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/portfolios' #dynamically retrieves db url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #off as modifications require extra memory and is not necessary in this case
 
db = SQLAlchemy(app) #initialization of connection, stored in variable db



class Portfolios(db.Model):
    __tablename__ = 'portfolios'


    portfolio_id = db.Column(GUID(), primary_key = True, default = uuid.uuid4 , nullable = False) #char(32) in mysql
    user_id = db.Column(GUID(), nullable = False)
    time_created = db.Column(db.DateTime(), nullable=False)
    last_updated = db.Column(db.DateTime(), nullable = False)
    
 
    def __init__(self, user_id, time_created, last_updated): #constructor. initializes record
        self.user_id = user_id
        self.time_created = time_created
        self.last_updated = last_updated
 
    def json(self): #returns json representation of the table in dict form
        return {"portfolio_id": self.portfolio_id, "user_id": self.user_id, "time_created": self.time_created, "last_updated":self.last_updated} 



@app.route("/get_all_portfolios") #get all portfolios
def get_all():
    portfolios = Portfolios.query.all() #SQLAlchemy magic
    if len(portfolios):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "portfolios": [portfolio.json() for portfolio in portfolios] #returns list of portfolios in json format
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no portfolios."
        }
    ), 404 #if status code is not specified, 200 OK is returned by default -- hence error 404 code is needed.


@app.route("/get_portfolio/<string:portfolio_id>")
def find_by_portfolio_id(portfolio_id):
    portfolio = Portfolios.query.filter_by(portfolio_id=portfolio_id).first() #returns a list of 1 item, .first() gets the first item. similar to limit 1 in sql
    if portfolio:
        return jsonify(
            {
                "code": 200,
                "data": portfolio.json()
            }
        )

    return jsonify(
        {
            "code": 404,
            "message": f"Portfolio {portfolio_id} not found"
        }
    ), 404

@app.route("/get_portfolio/user_find/<string:user_id>")
def find_by_user_id(user_id):
    portfolio = Portfolios.query.filter_by(user_id=user_id).first() #returns a list of 1 item, .first() gets the first item. similar to limit 1 in sql
    if portfolio:
        return jsonify(
            {
                "code": 200,
                "data": portfolio.json()
            }
        )

    return jsonify(
        {
            "code": 404,
            "message": f"Portfolio {user_id} not found"
        }
    ), 404

@app.route("/<string:user_id>/add_portfolio", methods=['POST'])
def create_portfolio(user_id): #create portfolio

    try:
        #query user
        #user don't exist: throw error
        #return 404 error coz user dont exist
        #use invokes and endpoint for user
        #else:
        portfolio = Portfolios(user_id = user_id, time_created = datetime.now(), last_updated = datetime.now()) #portfolio_id auto generated

        db.session.add(portfolio)
        #add portfolio to user
        db.session.commit()
        return jsonify(
            {
                "code": 201,
                "data": portfolio.json()
            }
        ), 201

    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        ex_str = str(exc_obj) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
        print(ex_str)
        return jsonify(
            {
                "code": 500,
                "data": {
                    "user_id": user_id
                },
                "message": "An error occurred creating the porfolio for this user."
            }
        ), 500



@app.route("/update_portfolio/<string:portfolio_id>", methods = ['PUT'])
def update_portfolio(portfolio_id):
    try:
        if (Portfolios.query.filter_by(portfolio_id = portfolio_id).first()): #book found
                data = request.get_json() #gets json data from the body of the request
                to_update = Portfolios.query.filter_by(portfolio_id = portfolio_id).first()
                to_update.last_updated = datetime.now()

                #the other fields of portfolio should not have any changes since they are mostly keys, and time_created of a portfolio should never change

                return jsonify( #portfolio successfully updated
                    {
                        "code": 201,
                        "data": to_update.json()
                    }
                ), 201 
        else:
            return jsonify( #portfolio not found
                {
                    "code": 404,
                    "message": f"Portfolio {portfolio_id} not found"
                }
            ), 404
    except:
        return jsonify( #error in updating
            {
                "code": 500,
                "data": {
                    "portfolio_id" : portfolio_id
                },
            "message": f"An error occured updating the time for portfolio {portfolio_id}"
            }
        ), 500




@app.route("/delete_portfolio/<string:portfolio_id>", methods=['DELETE'])
def delete_portfolio(portfolio_id):
    try:
        portfolio = Portfolios.query.filter_by(portfolio_id=portfolio_id).first()
        if portfolio:
            db.session.delete(portfolio)
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": {
                        "portfolio_id": portfolio_id
                    },
                    "message": f"Portfolio {portfolio_id} deleted"
                }
            )
        else:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "portfolio_id": portfolio_id
                    },
                    "message": f"Portfolio {portfolio_id} not found"
                }
            ), 404
    except:
            return jsonify(
                {
                    "code": 500,
                    "data": {
                        "portfolio_id": portfolio_id
                    },
                    "message": f"An error occured when trying to delete portfolio {portfolio_id}"
                }
            )


if __name__ == "__main__":
    app.run(port = 5003, debug = True) #adding host = 0.0.0.0 ensures that the service can be accessible in the network debug = true restarts the flask app if the source code is being changed as the flask app is running

#can specify which ip address and port that the flask app should start with, can communicate with other computers in this manner