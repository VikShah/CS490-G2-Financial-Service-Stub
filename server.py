from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pymysql.cursors
import random
import re

app = Flask(__name__)
CORS(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Ball9963@@##',
    'db': 'f_stub',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    connection = pymysql.connect(**db_config)
    return connection


@app.route('/check_credit_score', methods=['POST'])
def check_credit_score():
    ssn = request.json.get('ssn')

    if not ssn or not re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
        return jsonify({"error": "Invalid SSN format or missing SSN"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if SSN exists
            cursor.execute("""
                SELECT credit_score FROM users WHERE ssn = %s
            """, (ssn,))
            user = cursor.fetchone()

            if user:
                return jsonify({"credit_score": user['credit_score']})

            # If SSN does not exist, insert new user and credit score
            new_credit_score = random.randint(300, 850)
            cursor.execute("INSERT INTO users (ssn, credit_score) VALUES (%s, %s)", (ssn, new_credit_score))
            connection.commit()
            return jsonify({"credit_score": new_credit_score})

    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

@app.route('/verify_or_create_user', methods=['POST'])
def verify_or_create_user():
    data = request.json
    ssn = data.get('ssn')
    full_name = data.get('full_name')
    routing_number = data.get('routing_number')
    account_number = data.get('account_number')

    # Validate input format
    if not ssn or not full_name or not routing_number or not account_number:
        return jsonify({"error": "All fields are required"}), 400
    if not re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
        return jsonify({"error": "Invalid SSN format"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if the user exists
            cursor.execute("""
                SELECT user_id, full_name FROM users
                WHERE ssn = %s
            """, (ssn,))
            user = cursor.fetchone()

            if user:
                # Check if the existing user's full name matches the provided full name
                if user['full_name'] != full_name:
                    return jsonify({"error": "Full name does not match the provided SSN"}), 400
                return jsonify({"result": True})

            # If user does not exist, create a new user with a random credit score
            new_credit_score = random.randint(300, 850)
            cursor.execute("""
                INSERT INTO users (ssn, full_name, credit_score, last_request_date)
                VALUES (%s, %s, %s, NOW())
            """, (ssn, full_name, new_credit_score))
            connection.commit()

            return jsonify({"result": True, "credit_score": new_credit_score})

    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
