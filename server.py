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
    'password': '',
    'db': '',
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

@app.route('/get_user_id_by_ssn', methods=['GET'])
def get_user_id_by_ssn():
    # Get the SSN from the query parameters
    ssn = request.args.get('ssn')

    # Validate SSN input
    if not ssn or not re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
        return jsonify({"error": "Invalid or missing SSN"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Execute a query to find the user ID based on the SSN
            cursor.execute("SELECT user_id FROM users WHERE ssn = %s", (ssn,))
            user = cursor.fetchone()

            if user:
                return jsonify({"user_id": user['user_id']})
            else:
                return jsonify({"error": "No user found with the provided SSN"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()



@app.route('/create_or_update_account', methods=['POST'])
def create_or_update_account():
    data = request.json
    ssn = data.get('ssn')
    full_name = data.get('full_name')
    routing_number = data.get('routing_number')
    account_number = data.get('account_number')
    bank_name = data.get('bank_name')

    if not (ssn and full_name and routing_number and account_number and bank_name):
        print(ssn+' '+full_name)
        return jsonify({"error": "All fields are required"}), 400
    if not re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
        print(ssn)
        return jsonify({"error": "Invalid SSN format"}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id, full_name FROM users WHERE ssn = %s", (ssn,))
            user = cursor.fetchone()

            if user:
                if user['full_name'] != full_name:
                    print(user["full_name"])
                    return jsonify({"error": "Full name does not match the provided SSN"}), 400
                user_id = user['user_id']
            else:
                # Insert new user with random credit score
                new_credit_score = random.randint(300, 850)
                cursor.execute("INSERT INTO users (ssn, full_name, credit_score) VALUES (%s, %s, %s)", (ssn, full_name, new_credit_score))
                user_id = cursor.lastrowid
                connection.commit()

            # Check for existing bank account and update or insert accordingly
            cursor.execute("SELECT account_id FROM bank_accounts WHERE user_id = %s AND routing_number = %s AND account_number = %s", (user_id, routing_number, account_number))
            account = cursor.fetchone()
            if account:
                cursor.execute("UPDATE bank_accounts SET bank_name = %s WHERE account_id = %s", (bank_name, account['account_id']))
            else:
                cursor.execute("INSERT INTO bank_accounts (user_id, routing_number, account_number, bank_name) VALUES (%s, %s, %s, %s)", (user_id, routing_number, account_number, bank_name))
            connection.commit()
            return jsonify({"result": True, "message": "Account created or updated successfully"})
    except Exception as e:
        connection.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


@app.route('/create_loan_and_payment', methods=['POST'])
def create_loan_and_payment():
    data = request.json
    ssn = data.get('ssn')
    loan_amount = data.get('loan_amount')
    monthly_amount = data.get('monthly_amount')
    initial_payment_amount = data.get('initial_payment_amount')

    if not (ssn and loan_amount and monthly_amount and initial_payment_amount):
        return jsonify({"error": "All fields including SSN and payment details are required"}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Fetch user_id using SSN
            cursor.execute("SELECT user_id FROM users WHERE ssn = %s", (ssn,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User not found"}), 404
            user_id = user['user_id']

            # Fetch the account_id using user_id
            cursor.execute("SELECT account_id FROM bank_accounts WHERE user_id = %s", (user_id,))
            account = cursor.fetchone()
            if not account:
                return jsonify({"error": "Bank account not found"}), 404

            # Insert into loans and payments table
            cursor.execute("INSERT INTO loans (account_id, loan_amount, monthly_amount, insert_date, update_date) VALUES (%s, %s, %s, NOW(), NOW())", (account['account_id'], loan_amount, monthly_amount))
            loan_id = cursor.lastrowid
            cursor.execute("INSERT INTO payments (loan_id, payment_amount, payment_date, update_date) VALUES (%s, %s, NOW(), NOW())", (loan_id, initial_payment_amount))
            connection.commit()
            return jsonify({"success": True, "message": "Loan and initial payment created successfully", "loan_id": loan_id})
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


@app.route('/get_loan_details', methods=['POST'])
def get_loan_details():
    data = request.get_json()
    loan_id = data.get('loan_id')

    if not loan_id:
        return jsonify({"error": "Loan ID is required"}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Retrieve loan details
            cursor.execute("""
                SELECT loan_id, account_id, loan_amount, payment_sum, monthly_amount, insert_date, update_date
                FROM loans
                WHERE loan_id = %s
            """, (loan_id,))
            loan_details = cursor.fetchone()

            if not loan_details:
                return jsonify({"error": "No loan found with the provided ID"}), 404
            # Convert to dictionary to return as JSON


            return jsonify({"success": True, "loan_details": loan_details}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
