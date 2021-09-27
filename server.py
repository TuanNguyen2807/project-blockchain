import json
import sys
from blockchain import Blockchain
from flask import Flask, jsonify, request, render_template, redirect, url_for
import pymysql
import hashlib

# MySQL config
conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='project3')

# Initial flask
app = Flask(__name__)
checkLogin = False

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/login', methods = ['GET', 'POST'])
def signIn():
    error = None
    global checkLogin
    checkLogin = False
    if request.method == 'POST':
        global _usr
        # Get username and password from client
        _usr = request.form['usr']
        _pwd = request.form['pwd']
        try:
            
            cursor = conn.cursor()
            query="SELECT password FROM user WHERE username = %s"
            cursor.execute(query, _usr)
            result = cursor.fetchone()

            #Check if password is true
            if result[0] == _pwd:
                checkLogin = True

                # Get hashid
                query = "SELECT hashid FROM user WHERE username = %s"
                cursor.execute(query, _usr)
                result = cursor.fetchone()
                conn.commit()
                return redirect(url_for('index', hashid = result[0]))
            else:
                error = "Invalid User or Password"  
        except:
            error = "Invalid User or Password" 
    
    return render_template('LOGIN.html', error = error)

@app.route('/register', methods = ['GET', 'POST'])
def signUp():
    error = None
    global checkLogin
    checkLogin = False
    
    if request.method == 'POST':
        try:
            cursor = conn.cursor()
            
            #Get data from client
            _name = request.form['fullname']
            _usr = request.form['usr']
            _pwd = request.form['pwd']
            _con_pwd = request.form['con-pwd']
            if _name == '' or _usr == '' or _pwd == '' or _con_pwd == '':  #If not fill all input
                error = 'Please fill in all input'
            else:
                if _pwd != _con_pwd:
                    error = 'Password and Re-enter password are not equal'
                else: 
                    # Check user exist
                    query = 'SELECT * FROM user where username = %s'
                    cursor.execute(query, _usr)
                    if cursor.fetchone():
                        error = 'This username has existed'
                    else:
                        #Insert in to db
                        _hashid = hashlib.sha256(str(_usr).encode('utf-8')).hexdigest()
                        query = 'INSERT INTO user (username, password, hashid, coin) VALUES (%s, %s, %s, 0)'
                        cursor.execute(query, (_usr, _pwd, _hashid))
                        conn.commit()
                        return redirect(url_for('signIn'))
        except Exception as e:
            return jsonify({'error': str(e)})

    return render_template('REGISTER.html', error = error)

@app.route('/', methods = ['GET', 'POST'])
def default():
    return render_template('default.html')

@app.route('/<hashid>', methods = ['GET', 'POST'])
def index(hashid):
    if checkLogin == True:
        # Check hashid existed
        cursor = conn.cursor()
        query = 'SELECT * FROM user WHERE hashid = %s'
        cursor.execute(query, hashid)
        result = cursor.fetchone()
        if not bool(result):
            return 'Not Found', 404

        # Get coin
        query = 'SELECT coin FROM user WHERE hashid = %s'
        cursor.execute(query, hashid)
        result = cursor.fetchone()
        return render_template('index.html', hashid = hashid, coin = result[0])
    else:
        return redirect(url_for('signIn'))

@app.route('/mine', methods=['GET', 'POST'])
def mine():
    # Get hashid data
    hashid = request.data.decode('ascii')
    # Run proof of work algorithm to get the next proof

    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is '0' to signify that this node has mined a new coin
    blockchain.new_transaction(
        sender = '0',
        recipient = hashid,
        amount = 1,
        content = 'Mined',
    )

    # Forge the new Block by adding it to the chain
    block = blockchain.new_block(proof)

    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    cursor = conn.cursor()
    query = 'SELECT coin FROM user WHERE hashid = %s'
    cursor.execute(query, hashid)
    result = cursor.fetchone()
    real_amount = result[0]
    real_amount += 1
    query = 'UPDATE user SET coin = %s WHERE hashid = %s'
    cursor.execute(query, (real_amount, hashid))
    conn.commit()

    return jsonify(response), 200

@app.route('/transactions', methods=['POST'])
def new_transaction():
    values = request.data
    values = values.decode('ascii')
    jsonvalues = json.loads(values)
    print(jsonvalues)
    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'content']
    if not all(k in values for k in required):
        return 'Missing parameters', 400

    # Check in database
    cursor = conn.cursor()
    query = 'SELECT * FROM user WHERE hashid = %s'
    cursor.execute(query, str(jsonvalues['recipient']))
    result = cursor.fetchone()
    if not bool(result):
        return 'Recipient is not exist', 400

    # Check amount
    query = 'SELECT coin FROM user WHERE hashid = %s'
    cursor.execute(query, str(jsonvalues['sender']))
    result = cursor.fetchone()
    real_amount = result[0]
    if int(real_amount) < int(jsonvalues['amount']):
        return 'Your coin is not enough', 400

    # Update coin data
    real_amount -= int(jsonvalues['amount'])
    query = 'SELECT coin FROM user WHERE hashid = %s'
    cursor.execute(query, str(jsonvalues['recipient']))
    result = cursor.fetchone()
    recipient_coin = result[0]
    recipient_coin += int(jsonvalues['amount'])
    query = 'UPDATE user SET coin = %s WHERE hashid = %s'
    cursor.execute(query, (real_amount, str(jsonvalues['sender'])))
    query = 'UPDATE user SET coin = %s WHERE hashid = %s'
    cursor.execute(query, (recipient_coin, str(jsonvalues['recipient'])))

    # Crate a new transaction
    index = blockchain.new_transaction(jsonvalues['sender'], jsonvalues['recipient'], jsonvalues['amount'], jsonvalues['content'])

    response = {
        'message': f'Transaction will be added to Block {index}',
    }

    # Update transaction to database
    query = 'INSERT INTO contract (sender, recipient, amount, content) VALUES (%s, %s, %s, %s)'
    cursor.execute(query, (str(jsonvalues['sender']), str(jsonvalues['recipient']), str(jsonvalues['amount']), str(jsonvalues['content'])))
    conn.commit()

    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': "Our chain was replaced",
            'new_chain': blockchain.chain,
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain,
        }

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port listening')
    args = parser.parse_args()
    port = args.port
    app.run(host='127.0.0.1', port=port)
