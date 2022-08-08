from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from invokes import invoke_http
from GUID import GUID
import os,sys
from flask_cors import CORS
import logging
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/positions' #dynamically retrieves db url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #off as modifications require extra memory and is not necessary in this case
 
db = SQLAlchemy(app) #initialization of connection, stored in variable db
 


class Positions(db.Model):
    __tablename__ = 'positions'


    portfolio_id = db.Column(GUID(), nullable = False, primary_key = True)
    ticker = db.Column(db.String(120), nullable = False, primary_key = True)
    total_bought_at = db.Column(db.Float(), nullable = False)
    total_sold_at = db.Column(db.Float(), nullable = False)
    total_quantity = db.Column(db.Integer, nullable = False)
    last_bought_price = db.Column(db.Float(), nullable = False)
    last_sold_price = db.Column(db.Float()) #can be nullable since first transaction is buy and has no last sold price
    last_updated_price = db.Column(db.Float()) #can be nullable
    last_transaction_status = db.Column(db.String(120), nullable = False) 
    last_transaction_quantity = db.Column(db.Integer, nullable = False)
    last_updated = db.Column(db.DateTime(), nullable = False)
 
 
    def __init__(self, portfolio_id, ticker, total_bought_at, total_sold_at, total_quantity, last_bought_price, last_sold_price, last_updated_price, last_transaction_status, last_transaction_quantity,  last_updated): #constructor. initializes record
        self.portfolio_id = portfolio_id
        self.ticker = ticker
        self.total_bought_at = total_bought_at
        self.total_sold_at = total_sold_at
        self.total_quantity = total_quantity
        self.last_bought_price = last_bought_price
        self.last_sold_price = last_sold_price
        self.last_updated_price = last_updated_price
        self.last_transaction_status = last_transaction_status
        self.last_transaction_quantity = last_transaction_quantity
        self.last_updated = last_updated
 
    def json(self): #returns json representation of the table in dict form
        return {"portfolio_id": self.portfolio_id, "ticker":self.ticker, "total_bought_at": self.total_bought_at, "total_sold_at": self.total_sold_at, "quantity": self.total_quantity, "last_bought_price": self.last_bought_price, "last_sold_price": self.last_sold_price, "last_updated": self.last_updated} 

@app.route("/get_all_positions") #get all positions
def get_all():
    positions = Positions.query.all() #SQLAlchemy magic
    if positions:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "position": [position.json() for position in positions] #returns list of portfolios in json format
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no positions."
        }
    ), 404 #if status code is not specified, 200 OK is returned by default -- hence error 404 code is needed.


@app.route("/get_positions/<string:portfolio_id>")
def get_all_positions_by_portfolio_id(portfolio_id):
    positions = Positions.query.filter_by(portfolio_id=portfolio_id)#returns a list of positions
    if positions:
        return jsonify(
            {
                "code": 200,
                "data": [position.json() for position in positions]
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": f"No positions for {portfolio_id} found"
        }
    ), 404

@app.route("/get_positions/<string:portfolio_id>/<string:ticker>")
def get_ticker_by_portfolio_id(portfolio_id, ticker):
    position = Positions.query.filter_by(portfolio_id = portfolio_id, ticker = ticker).first()#returns a list of 1 item, .first() gets the first item. similar to limit 1 in sql
    if position:
        return jsonify(
            {
                "code": 200,
                "data": position.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                    "portfolio_id" : portfolio_id,
                    "ticker": ticker
            },
            "message": f"No positions in {ticker} for {portfolio_id} found"
        }
    ), 404    

@app.route("/add_position/<string:portfolio_id>", methods=['POST'])
def add_position(portfolio_id): #add position

    data = request.get_json() #gets json data from the body of the request
    ##getting values from request json body
    ticker = data['ticker']
    quantity = data['quantity']
    buy_price = data['price']

    try:

        if(Positions.query.filter_by(portfolio_id = portfolio_id, ticker = ticker).first()):
            return jsonify(
            {
                "code": 400,
                "data": {
                    "portfolio_id": portfolio_id
                },
                "message": f"Portfolio {portfolio_id} already has positions in {ticker}. Please update instead."
            }
        ), 400


        added_position = Positions(portfolio_id = portfolio_id, ticker = ticker, total_bought_at = quantity * buy_price, total_sold_at = 0.0, total_quantity = quantity, last_bought_price = buy_price, last_sold_price = 0.0, last_updated_price = buy_price, last_transaction_status = "buy", last_transaction_quantity = quantity, last_updated = datetime.now()) #create position record to be added to db
        db.session.add(added_position)
        #added_position.portfolio.last_updated = datetime.now()
        db.session.commit()
        return jsonify( #return added_position
            {
                "code" : 200,
                "data": added_position.json() 
            }
        ), 200

    #add in last updated here

    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        ex_str = str(exc_obj) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
        print(ex_str)
        return jsonify(
            {
                "code": 500,
                "data": {
                    "portfolio_id": portfolio_id,
                    "position": added_position.json()
                },
                "message": f"An error occurred adding the position for portfolio {portfolio_id}"
            }
        ), 500

@app.route("/update_position/<string:portfolio_id>", methods = ['PUT'])
def update_position(portfolio_id):
    data = request.get_json()
    ticker = data['ticker']
    try:
        if (Positions.query.filter_by(portfolio_id = portfolio_id, ticker = ticker).first()): #position found
                to_update = Positions.query.filter_by(portfolio_id = portfolio_id).first() #get position record via query and filter

                # to_update.total_quantity = 10
                if data['last_bought_price']:
                    to_update.last_bought_price = data['last_bought_price']
                if data['last_sold_price']:
                    to_update.last_sold_price = data['last_sold_price']
                if data['last_transaction_quantity']:
                    to_update.last_transaction_quantity = data['last_transaction_quantity']
                if data['last_transaction_status']:
                    to_update.last_transaction_status = data['last_transaction_status']
                if data['last_updated_price']:
                    to_update.last_updated_price = data['last_updated_price']
                if data['total_bought_at']:
                    to_update.total_bought_at = data['total_bought_at']
                if data['total_sold_at']:
                    to_update.total_sold_at = data['total_sold_at']
                if data['total_quantity']:
                    to_update.total_quantity = data['total_quantity'] 


                to_update.last_updated = datetime.now()
                
                db.session.commit()

                return jsonify( #portfolio successfully updated
                    {
                        "code": 201,
                        "data": to_update.json()
                    }
                ), 201 

        else:
            return jsonify( #position not found
                {
                    "code": 404,
                    "data": {
                            "portfolio_id" : portfolio_id,
                            "ticker": ticker
                    },
                    "message": f"No positions in {ticker} for {portfolio_id} found"
                }
            ), 404            

    except:
        return jsonify( #error in updating
            {
                "code": 500,
                "data": {
                    "portfolio_id" : portfolio_id,
                    "ticker": ticker
                },
            "message": f"An error occured updating {ticker} for portfolio {portfolio_id}"
            }
        ), 500




@app.route("/delete_portfolio/<string:portfolio_id>/<string:ticker>", methods=['DELETE'])
def delete_position(portfolio_id, ticker):
    try:
        deleted_position = Positions.query.filter_by(portfolio_id=portfolio_id, ticker = ticker).first()
        if deleted_position:
            db.session.delete(deleted_position)
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": {
                        "portfolio_id": portfolio_id,
                        "ticker": ticker
                    },
                    "message": f"{ticker} in portfolio {portfolio_id} deleted"
                }
            )
        else:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                            "portfolio_id" : portfolio_id,
                            "ticker": ticker
                    },
                    "message": f"No positions in {ticker} for {portfolio_id} found"
                }
            ), 404

    except:
            return jsonify(
                {
                    "code": 500,
                    "data": {
                        "portfolio_id": portfolio_id,
                        "ticker": ticker
                    },
                    "message": f"An error occured when trying to delete ticker {ticker} in portfolio {portfolio_id}"
                }
            )


if __name__ == "__main__":
    app.run(port = 5004, debug = True) #adding host = 0.0.0.0 ensures that the service can be accessible in the network debug = true restarts the flask app if the source code is being changed as the flask app is running

#can specify which ip address and port that the flask app should start with, can communicate with other computers in this manner