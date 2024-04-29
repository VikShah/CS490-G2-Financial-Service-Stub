from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
import random
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12abAB@#'
app.config['MYSQL_DB'] = 'f_stub'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def is_valid_card_number(number):
    """ Validate the card number using regex or Luhn's algorithm """
    return re.match(r'^\d{16}$', number)

def is_valid_cvc(cvc):
    """ Validate CVC code, typically 3-4 digits """
    return re.match(r'^\d{3,4}$', cvc)

@app.route('/credit_score', methods=['POST'])
def credit_score():
    try:
        card_number = request.json.get('card_number')
        cvc = request.json.get('cvc')

        if not card_number or not cvc or not is_valid_card_number(card_number) or not is_valid_cvc(cvc):
            return jsonify({"error": "Invalid input"}), 400

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT credit_score FROM f_stub.card_info 
            JOIN f_stub.card_account ON f_stub.card_info.card_number = f_stub.card_account.card_number 
            JOIN f_stub.account_info ON f_stub.card_account.account_id = f_stub.account_info.account_id 
            WHERE f_stub.card_info.card_number = %s AND f_stub.card_info.security_code = %s
        """, (card_number, cvc))
        account = cur.fetchone()

        if account:
            return jsonify({"credit_score": account['credit_score']})
        else:
            # Generate a random credit score
            new_credit_score = random.randint(300, 850)
            cur.execute("INSERT INTO f_stub.account_info (credit_score, last_request_date) VALUES (%s, NOW())", (new_credit_score,))
            account_id = cur.lastrowid
            cur.execute("INSERT INTO f_stub.card_account (card_number, account_id) VALUES (%s, %s)", (card_number, account_id))
            cur.execute("INSERT INTO f_stub.card_info (card_number, security_code) VALUES (%s, %s)", (card_number, cvc))
            mysql.connection.commit()
            cur.close()
            return jsonify({"new_credit_score": new_credit_score})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
