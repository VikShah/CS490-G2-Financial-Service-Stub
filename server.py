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



#recieves ssn and fullname and returns a credit score
@app.route('/check_credit_score', methods=['POST'])
def check_credit_score():
    ssn = request.json.get('ssn')
    full_name = request.json.get('full_name')

    if not ssn or not full_name or not re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
        return jsonify({"error": "Invalid SSN format or missing name"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if SSN exists and compare full name
            cursor.execute("""
                SELECT users.user_id, full_name, credit_score FROM users
                JOIN account_info ON users.user_id = account_info.user_id
                WHERE users.ssn = %s AND users.full_name = %s
            """, (ssn,full_name))
            user = cursor.fetchone()

            if user:
                if user['full_name'] != full_name:
                    return jsonify({"error": "Full name does not match the provided SSN"}), 400
                return jsonify({"credit_score": user['credit_score']})

            # If SSN does not exist, insert new user and credit score
            new_credit_score = random.randint(300, 850)
            cursor.execute("INSERT INTO users (ssn, full_name) VALUES (%s, %s)", (ssn, full_name))
            user_id = connection.insert_id()
            cursor.execute("INSERT INTO account_info (user_id, credit_score, last_request_date) VALUES (%s, %s, NOW())", (user_id, new_credit_score))
            connection.commit()
            return jsonify({"credit_score": new_credit_score})

    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


#checks if card belongs to customer
@app.route('/verify_card_ownership', methods=['POST'])
def verify_card_ownership():
    data = request.json
    ssn = data.get('ssn')
    card_number = data.get('card_number')
    security_code = data.get('security_code')
    full_name = data.get('full_name')
    expiry_month = data.get('expiry_month')
    expiry_year = data.get('expiry_year')

    # Validate inputs
    if not (ssn and card_number and security_code and full_name and expiry_month and expiry_year and
            re.match(r'^\d{3}-\d{2}-\d{4}$', ssn) and
            re.match(r'^\d{16}$', card_number) and
            re.match(r'^\d{3,4}$', security_code) and
            1 <= int(expiry_month) <= 12 and
            int(expiry_year) >= datetime.now().year):
        return jsonify({"error": "Invalid input"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT users.ssn FROM users
                LEFT JOIN account_info ON users.user_id = account_info.user_id
                LEFT JOIN card_account ON account_info.account_id = card_account.account_id
                LEFT JOIN card_info ON card_account.card_number = card_info.card_number
                WHERE users.ssn = %s AND card_info.card_number = %s AND card_info.security_code = %s AND users.full_name = %s
                  AND card_info.expiry_month = %s AND card_info.expiry_year = %s
            """, (ssn, card_number, security_code, full_name, expiry_month, expiry_year))
            result = cursor.fetchone()

            return jsonify({"result": bool(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

#add news card associated with that user
@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.get_json()
    ssn = data.get('ssn')
    card_number = data.get('card_number')
    security_code = data.get('security_code')
    expiry_month = data.get('expiry_month')
    expiry_year = data.get('expiry_year')

    if not (ssn and card_number and security_code and expiry_month and expiry_year):
        return jsonify({"error": "All fields are required"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE ssn = %s", (ssn,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User not found"}), 404

            user_id = user['user_id']

            # Check if card already exists
            cursor.execute("SELECT card_number FROM card_account WHERE card_number = %s", (card_number,))
            if cursor.fetchone():
                return jsonify({"error": "Card already exists"}), 409

            # Get or create account_id for this user
            cursor.execute("SELECT account_id FROM account_info WHERE user_id = %s", (user_id,))
            account_info = cursor.fetchone()
            if not account_info:
                cursor.execute("INSERT INTO account_info (user_id, credit_score, last_request_date) VALUES (%s, NULL, NOW())", (user_id,))
                account_id = connection.insert_id()
            else:
                account_id = account_info['account_id']

            # Insert card account
            cursor.execute("INSERT INTO card_account (card_number, account_id) VALUES (%s, %s)", (card_number, account_id))

            # Insert card info
            cursor.execute("INSERT INTO card_info (card_number, security_code, expiry_month, expiry_year) VALUES (%s, %s, %s, %s)", 
                           (card_number, security_code, expiry_month, expiry_year))
            
            connection.commit()
            return jsonify({"success": "Card added successfully"}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
