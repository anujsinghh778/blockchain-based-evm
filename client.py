from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')

# REGISTER USER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        try:
            response = requests.post('http://127.0.0.1:5001/register', json={'voter_id': voter_id})
            if response.status_code == 200:
                msg = response.json().get('message', 'Registered successfully!')
            else:
                msg = f"Error: {response.text}"
        except Exception as e:
            msg = f"Server error: {e}"
        return render_template('register.html', message=msg)
    return render_template('register.html')

# VOTE ENDPOINT (Frontend sends vote)
@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    data = request.get_json()
    candidate = data.get('candidate')
    voter_id = data.get('voter_id')
    try:
        response = requests.post('http://127.0.0.1:5001/vote', json={'candidate': candidate, 'voter_id': voter_id})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Voting server error: {e}'})

# SHOW RESULTS
@app.route('/results', methods=['GET'])
def results():
    try:
        response = requests.get('http://127.0.0.1:5001/results')
        data = response.json()
        results = data.get('results', [])
    except Exception:
        results = []
    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(port=5000)
