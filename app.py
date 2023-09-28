from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient


app = Flask(__name__)


try: # This try operator checks the connection to MongoDB.
    connection = MongoClient('mongodb://localhost:27017/') #Specifies a MongoDB that is run on a local computer & the port number.
    connection.server_info() # Provides information about the server.
    print("Connected to MongoDB")
except Exception as error: # Prints an error if the connection fails.
    print(f"MongoDB connection failed: {error}")

db = connection['ma_avs_addresses'] # Specifies the name of the database being connected to
collection = db['ma_avs_addresses'] # Specifies the collection

@app.route('/') # The address entry page
def run_ui():
    return render_template('user_ui.html')

@app.route('/submitAddress', methods=['POST']) # Defines the root that handles POST requests to the endpoint, which is defined as '/submitAddress'
def submit_address():
    try:
        # Obtains JSON data from request
        data = request.get_json()
        # Validate and process the data
        entered_address = data.get('addressLine1') # Gets the selected data out of the JSON data
        # Query the MongoDB database looking for a match to addressLine1
        found_match = collection.find_one({'addressLine1' : entered_address})

        
        # Determines if a matching address was found
        valid_address = found_match is not None
        
        # Creates a response
        response = {'validAddress': valid_address, 'message': 'Address is valid.' if valid_address else 'Address is not valid.'} 
        return jsonify(response), 200
    except Exception as error: # Handles server errors
        return jsonify({f'error': 'Internal server error: {error}'}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
