from uuid import uuid4
import json
import sys
from blockchain import Blockchain
from flask import Flask, jsonify, request, render_template, redirect, url_for
import pymysql

# MySQL config
conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='project3')

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-','')

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
                    #Insert in to db
                    query = 'INSERT INTO user (username, password, hashid, coin) VALUES (%s, %s, %s, 0)'
                    cursor.execute(query, (_usr, _pwd, _usr))
                    #Create data for userid

                    checkLogin = True

                    # Get userid
                    query = "SELECT hashid FROM user WHERE username = %s"
                    cursor.execute(query, _usr)
                    result = cursor.fetchone()
                    hashid = result[0]
                    return redirect(url_for('index', hashid = hashid))
        except Exception as e:
            return jsonify({'error': str(e)})

    return render_template('REGISTER.html', error = error)

@app.route('/<hashid>', methods = ['GET', 'POST'])
def index(hashid):
    return render_template('index.html', hashid = hashid)

@app.route('/mine', methods=['GET'])
def mine():
    # Run proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is '0' to signify that this node has mined a new coin
    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1,
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
    return jsonify(response), 200

@app.route('/transactions', methods=['POST'])
def new_transaction():
    values = request.data
    values = values.decode('ascii')
    jsonvalues = json.loads(values)
    print(jsonvalues)
    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing parameters', 400

    # Crate a new transaction
    index = blockchain.new_transaction(jsonvalues['sender'], jsonvalues['recipient'], jsonvalues['amount'])

    response = {
        'message': f'Transaction will be added to Block {index}',
    }
   
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
    return jsonify(response), 201


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
