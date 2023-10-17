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
        entered_addresslineone = data.get('addressLine1') # Gets the selected data out of the JSON data
        entered_city = data.get('city')
        entered_state = data.get('stateorprovince') # Gets the selected data out of the JSON data
        entered_country = data.get('country')
        entered_zip = data.get('zip') # Gets the selected data out of the JSON data
        entered_zipplusfour = data.get('zip +4')       
        # Query the MongoDB database looking for a match to addressLine1
        found_match = collection.find_one({
             '$or' :[
            
           { 'addressLine1' : entered_addresslineone,
                                        'city' : entered_city,
                                        'stateorprovince' : entered_state,
                                           'country' : entered_country,
                                        },
                                                                                 
                                   
                                  {
                                        'zip' : entered_zip,
                                       'zipplusfour' : entered_zipplusfour,}
]
   })

        if found_match.get('zip') == entered_zip:
            zip_match = True

        valid_address = found_match is not None

        address_match = found_match.get('addressLine1') == entered_addresslineone and found_match.get('city') == entered_city and found_match.get('stateorprovince') == entered_state and found_match.get('country') == entered_country

        zip_match = found_match.get('zip') == entered_zip

        perfect_match = address_match and zip_match






                                                        
        # Creates a response
        response = {'validAddress': valid_address,'matchType':perfect_match, 'message': 'Address is valid; match found.' if valid_address else 'Address is not valid.'} 
        return jsonify(response), 200
    except Exception as error: # Handles server errors
        return jsonify({f'error': 'Internal server error: {error}'}), 500


if __name__ == "__main__":
    app.run()
