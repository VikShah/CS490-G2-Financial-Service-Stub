from flask import Flask, request, jsonify
import pymysql
from flask_cors import CORS 
from shapely.geometry import Point
from datetime import datetime, timedelta, timezone
from pymysql.err import MySQLError
import random

app = Flask(__name__)
CORS(app) 

HOST = "localhost"
USER = "root"
PASSWORD = ""
DB = "CS490"


@app.route("/assignCreditScore", methods=['POST'])
def assignCreditScore():
    db = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB)
    data = request.get_json()
    #See if user has a credit score
    user_id = data.get("userID")
    with db.cursor() as cursor:
        query = """SELECT score 
                    FROM creditScore WHERE user_id = %s"""
        cursor.execute(query, ([user_id]))
        results = cursor.fetchall()
        if results:
            return jsonify(results), 200
    #If user has no credit score, assign them one randomly and return it
    scores = [757, 763, 785, 660, 701, 584, 642, 619, 563, 555]
    u_credit_score = scores[random.randint(0,9)]
    with db.cursor() as cursor:
        query = """INSERT INTO creditScore (user_id,score) values (%s,%s)"""
        cursor.execute(query, (user_id,u_credit_score))
        db.commit()
    return jsonify(u_credit_score)