from flask import Flask, request, jsonify
import pymysql
from flask_cors import CORS 
from shapely.geometry import Point
from datetime import datetime, timedelta, timezone
from pymysql.err import MySQLError
import random
import json

app = Flask(__name__)

#from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager

app = Flask(__name__)
CORS(app)

#jwt app token management
app.config["JWT_SECRET_KEY"] = "SecretKey"
#jwt = JWTManager(app)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
#end of jwt token management

HOST = "localhost"
USER = "root"
PASSWORD = "Minecraft928"
DB = "f_stub"

@app.route("/assignCreditScore", methods=['POST'])
def assignCreditScore():
    db = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB)
    data = request.get_json()
    #See if user has a credit score
    user_id = data.get("user_id")
    account_id = "100" + str(user_id)
    with db.cursor() as cursor:
        query = """SELECT credit_score  
                    FROM account_info 
                    WHERE account_id = %s"""
        cursor.execute(query, ([account_id]))
        results = cursor.fetchall()         
        if results:
            return jsonify(results), 200
    #If user has no credit score, assign them one randomly and return it
    scores = [757, 763, 785, 660, 701, 584, 642, 619, 563, 555]
    u_credit_score = scores[random.randint(0,9)]
    with db.cursor() as cursor:
        query = """INSERT INTO account_info (account_id,credit_score,last_request_date) values (%s,%s,NOW())"""
        cursor.execute(query, (account_id,u_credit_score))
        db.commit()
    return jsonify(u_credit_score)

@app.route("/addNewCard", methods=['POST'])
def addNewCard():
    db = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB)
    data = request.get_json()
    #See if card is already in database
    user_id = data.get("user_id")
    card_number = str(data.get("card_number"))
    card_number = card_number.replace("-","").replace(" ","")
    account_id = "100" + str(user_id)
    with db.cursor() as cursor:
        query = """SELECT card_number  
                    FROM card_account 
                    WHERE account_id = %s"""
        cursor.execute(query, ([account_id]))
        results = cursor.fetchall()         
        if results and results[0][0] == card_number:
            response = {
                'message': 'Card already exists'
            }
            return jsonify(response), 200   
    #If card is not already in database, enter it in. 
    security_code = data.get("security_code")
    with db.cursor() as cursor:
                query = """INSERT INTO card_account (card_number,account_id) values (%s,%s)"""
                cursor.execute(query, (card_number,account_id))
                db.commit()
    with db.cursor() as cursor:
                query = """INSERT INTO card_info (card_number,security_code) values (%s,%s)"""
                cursor.execute(query, (card_number,security_code))
                db.commit()
    response = {
        'message': 'Card information sucessfully added to database'
    }
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5005)
