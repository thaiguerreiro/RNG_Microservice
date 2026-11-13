from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/random', methods=['GET'])
def generate_random():
    # Receive bounds from the request
    min = request.args.get('min', type=int)
    max = request.args.get('max', type=int)

    # Validate inputs


    # Generate output
    result = 

    # Return result as JSON
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(port=5000, debug=True)