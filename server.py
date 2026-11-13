from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/random', methods=['GET'])
def generate_random():
    # Receive bounds from the request
    min = request.args.get('min', type=int)
    max = request.args.get('max', type=int)

    # Validate inputs
    if min is None or max is None:
        return jsonify({"error": "Both 'min' and 'max' parameters are required"}), 400

    if min >= max:
        return jsonify({"error": "'min' parameter must be less than 'max' parameter"}), 400

    # Generate output
    result = random.randint(min, max)

    # Return result as JSON
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(port=5000, debug=True)