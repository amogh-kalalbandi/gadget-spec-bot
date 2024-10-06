from flask import Flask, jsonify, request
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-mpnet-base-v2")
app = Flask(__name__)

@app.route('/vector', methods=['GET'])
def get_vector():
    # Get the 'input' query parameter from the URL
    input_param = request.args.get('input')
    
    if input_param is None:
        return jsonify({'error': 'No input parameter provided.'}), 400

    try:
        return jsonify({'vector': model.encode(input_param).tolist()})
    except ValueError:
        return jsonify({'error': 'Invalid input format. Use comma-separated numbers.'}), 400


if __name__ == '__main__':
    app.run(debug=True)