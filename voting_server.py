# voting_blockchain_server.py

from flask import Flask, request, jsonify
from facial_module import FacialRecognizer
import hashlib, json, time
from flask_cors import CORS


# --- Blockchain Class ---
class Blockchain:
    def __init__(self):
        self.chain = []
        self.difficulty = 4
        self.create_block(previous_hash='0', proof=1)

    def create_block(self, vote=None, previous_hash='', proof=None):
        previous_block = self.chain[-1] if self.chain else None
        previous_proof = previous_block['proof'] if previous_block else 1
        if proof is None:
            proof = self.proof_of_work(previous_proof)
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'vote': vote,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'proof': proof
        }
        block['hash'] = self.hash(block)
        self.chain.append(block)
        return block

    def proof_of_work(self, previous_proof):
        new_proof = 1
        while True:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:self.difficulty] == '0' * self.difficulty:
                return new_proof
            new_proof += 1

    @staticmethod
    def hash(block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            previous_block = self.chain[i - 1]
            current_block = self.chain[i]

            recalculated_previous_hash = self.hash(previous_block)
            if current_block['previous_hash'] != recalculated_previous_hash:
                return False

            block_copy = current_block.copy()
            del block_copy['hash']
            recalculated_block_hash = self.hash(block_copy)
            if current_block['hash'] != recalculated_block_hash:
                return False

            proof_hash = hashlib.sha256(str(current_block['proof']**2 - previous_block['proof']**2).encode()).hexdigest()
            if not proof_hash.startswith('0' * self.difficulty):
                return False

        return True


# --- App Setup ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
recognizer = FacialRecognizer()
blockchain = Blockchain()


# --- Registration ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    voter_id = data.get('voter_id') if data else None
    if not voter_id:
        return jsonify({'status': 'error', 'message': 'Voter ID is required'}), 400
    try:
        recognizer.register_user(voter_id)
        return jsonify({'status': 'success', 'message': f'{voter_id} registered successfully'})
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500



# --- Facial Recognition ---
@app.route('/recognize', methods=['GET'])
def recognize():
    voter_id = recognizer.recognize()
    if not voter_id:
        return jsonify({'status': 'error', 'message': 'Face not recognized'})
    if recognizer.has_already_voted(voter_id):
        return jsonify({'status': 'error', 'message': 'Already voted'})
    return jsonify({'status': 'success', 'voter_id': voter_id})


# --- Cast Vote via Blockchain ---
@app.route('/vote', methods=['POST'])
def vote():
    if not blockchain.is_chain_valid():
        return jsonify({'status': 'error', 'message': 'Blockchain integrity compromised!'}), 400

    data = request.get_json()
    voter_id = data.get('voter_id')
    candidate = data.get('candidate')

    if recognizer.has_already_voted(voter_id):
        return jsonify({'status': 'error', 'message': 'Duplicate vote'})

    # Store on blockchain
    previous_block = blockchain.chain[-1]
    proof = blockchain.proof_of_work(previous_block['proof'])
    new_block = blockchain.create_block(vote=candidate, proof=proof)

    return jsonify({
        'status': 'success',
        'message': 'Vote recorded securely',
        'block': {
            'index': new_block['index'],
            'timestamp': new_block['timestamp'],
            'vote': new_block['vote'],
            'hash': new_block['hash']
        }
    })


# --- Results ---
@app.route('/results', methods=['GET'])
def get_results():
    if not blockchain.is_chain_valid():
        return jsonify({
            'status': 'error',
            'message': 'Blockchain tampering detected! Results are not reliable.'
        }), 400

    results = {}
    for block in blockchain.chain[1:]:  # Skip genesis
        vote = block['vote']
        results[vote] = results.get(vote, 0) + 1

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return jsonify({
        'status': 'success',
        'results': [{'candidate': c, 'votes': v} for c, v in sorted_results]
    })


# --- Blockchain Utilities (Optional) ---
@app.route('/validate', methods=['GET'])
def validate_chain():
    return jsonify({'valid': blockchain.is_chain_valid()})


@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    return jsonify(blockchain.chain)


@app.route('/tamper', methods=['GET'])
def tamper_blockchain():
    if len(blockchain.chain) > 1:
        blockchain.chain[1]['vote'] = "Tampered Vote"
        return jsonify({'status': 'success', 'message': 'Blockchain tampered successfully!'})
    return jsonify({'status': 'error', 'message': 'No votes to tamper.'}), 400


# --- Run Server ---
if __name__ == '__main__':
    print("Running unified voting + blockchain server on port 5001")
    app.run(port=5001, debug=True)
