from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient
from fuzzywuzzy import fuzz, process
from bson.objectid import ObjectId

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

#@app.route('/submitAddress', methods=['POST']) # Defines the root that handles POST requests to the endpoint, which is defined as '/submitAddress'

@app.route('/entries')
def entry_list():
    # Retrieve a list of entries from the database
    entries = collection.find()
    return render_template('maintenance_screen.html', entries=entries)

@app.route('/entries-json')
def entry_list_json():
    try:
        entries = collection.find()

        # Convert entries to a list of dictionaries and convert ObjectId to string
        entry_list = [
            {**entry, '_id': str(entry['_id'])}  # Convert ObjectId to string
            for entry in entries
        ]

        return jsonify({'entries': entry_list})
    except Exception as e:
        print(f"Error in entry_list_json: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/maintenance_screen')
def database_management():
    # Logic to retrieve and display database entries
    return render_template('maintenance_screen.html')

@app.route('/new_entry', methods=['GET','POST'])
def new_entry():
    if request.method == 'POST':
        try:
            data = dict(request.form)
            collection.insert_one(data)
            return redirect(url_for('database_management'))
        except Exception as error:
            return jsonify({'error': f'Internal server error: {error}'}), 500

@app.route('/entry/<entry_id>')
def get_entry(entry_id):
    try:
        entry = collection.find_one({"_id": ObjectId(entry_id)})
        if entry:
            entry['_id'] = str(entry['_id'])  # Convert ObjectId to string
            return jsonify(entry)
        else:
            return jsonify({'error': 'Entry not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/edit_entry/<entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    if request.method == 'GET':
        # Display the edit form with existing entry data
        entry = collection.find_one({"_id": ObjectId(entry_id)})
        return render_template('maintenance_screen.html', entry=entry)
    elif request.method == 'POST':
        # Handle the form submission to update the entry
        data = request.form
        filter_criteria = {"_id": ObjectId(entry_id)}
        update_operation = {
            "$set": {
                "addressLine1": data.get("addressLine1"),
                "addressLine2": data.get("addressLine2"),
                "city": data.get("city"),
                "stateorprovince": data.get("stateorprovince"),
                "zip": data.get("zip"),
                "zipPlusFour": data.get("zipPlusFour"),
            }
        }

        # Perform the update operation in your MongoDB collection
        collection.update_one(filter_criteria, update_operation)

        # Redirect to the list of entries or a success page
        return redirect('/entries')


@app.route('/delete_entry/<entry_id>', methods=['POST'])
def delete_entry(entry_id):
    try:
        # Route that allows users to delete a database entry
        filter_criteria = {"_id": ObjectId(entry_id)}
        collection.delete_one(filter_criteria)
        return jsonify({'message': 'Entry deleted successfully'}), 200
    except Exception as error:
        return jsonify({'error': f'Internal server error: {error}'}), 500

#def fuzziness():
        #fuzzy_match = fuzz.token_set_ratio()

        #min_threshold = 80

        #return fuzzy_match >= min_threshold
@app.route('/submitAddress', methods=['POST'])
def submit_address():
    try:
        # Obtains JSON data from request
        data = request.get_json()
        # Validate and process the data
        entered_addresslineone = data.get('addressLine1') # Gets the selected data out of the JSON data
        entered_addresslinetwo = data.get('addressLine2') 
        entered_city = data.get('city')
        entered_state = data.get('stateorprovince') 
        entered_country = data.get('country')
        entered_zip = data.get('zip') 
        entered_zipplusfour = data.get('zipPlusFour')      

        found_address = []
        match_score = 0

        # Query the MongoDB database looking for a match to addressLine1
        found_match = collection.find_one({
             '$or' :[
            {'addressLine1' : entered_addresslineone,
             'addressLine2' : entered_addresslinetwo,
            'city' : entered_city,
            'stateorprovince' : entered_state,
            'country' : entered_country,
            'zip' : entered_zip,
            'zipPlusFour': entered_zipplusfour        
                                           },
           { 'addressLine1' : entered_addresslineone,
                                        'city' : entered_city,
                                        'stateorprovince' : entered_state,
                                           'country' : entered_country
                                        },
                                                                                 
                                   
                                  {
                                        'zip' : entered_zip
                                        }
]
   })

        #if found_match.get('zip') == entered_zip:
            #zip_match = True

        valid_address = found_match is not None

        address_match = (
            fuzz.ratio(found_match.get('addressLine1'), entered_addresslineone) > 80
        )
        address_match = (
                        found_match.get('addressLine1') == entered_addresslineone and
                        found_match.get('city') == entered_city and 
                        found_match.get('stateorprovince') == entered_state and 
                        found_match.get('country') == entered_country)

        zip_match = found_match.get('zip') == entered_zip

        partial_match = (zip_match == True or address_match == True) and not (zip_match == True and address_match == True)

        near_match = (
        found_match.get('addressLine1') == entered_addresslineone and 
        found_match.get('city') == entered_city and
        found_match.get('stateorprovince') == entered_state and
        found_match.get('country') == entered_country and
        found_match.get('zip') == entered_zip and
        (found_match.get('addressLine2') != entered_addresslinetwo or found_match.get('zipPlusFour') != entered_zipplusfour))

        perfect_match = (
        found_match.get('addressLine1') == entered_addresslineone and 
        found_match.get('city') == entered_city and
        found_match.get('stateorprovince') == entered_state and
        found_match.get('country') == entered_country and
        found_match.get('addressLine2') == entered_addresslinetwo and
        found_match.get('zip') == entered_zip and
        found_match.get('zipPlusFour') == entered_zipplusfour)
# Near match - 5 digit zip code
# Perfect match - zip code +4, addressLine2 if it's available

# What happens if there is a "perfect match in all fields but zip+4 or adddressLine2?"



                                                        
        # Creates a response
        response = {'validAddress': valid_address,
                    'perfectMatch': perfect_match,
                    'nearMatch': near_match, 
                    'partialMatch': partial_match,
                    #'matchingAddress': found_match,
                    'fuzzRatio':fuzz.ratio(found_match.get('addressLine1'), entered_addresslineone) > 80,
                    'message': f'Address is valid; match found. Match{found_match}' if valid_address else 'Address is not valid.'} 
        return jsonify(response), 200
    except Exception as error: # Handles server errors
        return jsonify({f'error': 'Internal server error: {error}'}), 500


if __name__ == "__main__":
    app.run()

