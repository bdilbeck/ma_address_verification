from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient
from fuzzywuzzy import fuzz, process
from bson.objectid import ObjectId
from bson.json_util import dumps, loads
from flask.json import jsonify


app = Flask(__name__)


try: # This try operator checks the connection to MongoDB.
    connection = MongoClient('mongodb://localhost:27017/') #Specifies a MongoDB that is run on a local computer & the port number.
    connection.server_info() # Provides information about the server.
    print("Connected to MongoDB")
except Exception as error: # Prints an error if the connection fails.
    print(f"MongoDB connection failed: {error}")


db = connection['ma_avs_addresses'] # Specifies the name of the database being connected to
collection = db['ma_avs_addresses2'] # Specifies the collection

@app.route('/') # The address entry page
def run_ui():
    return render_template('user_ui.html')

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
            entry['_id'] = str(entry['_id'])  # Converts ObjectId to string
            return jsonify(entry)
        else:
            return jsonify({'error': 'Entry not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/edit_entry/<entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    if request.method == 'GET':
        # Displays the edit form with existing entry data
        entry = collection.find_one({"_id": ObjectId(entry_id)})

        # Checks each field and replace 'None' with an empty string
        for key, value in entry.items():
            if value is None:
                entry[key] = ''

        return render_template('maintenance_screen.html', entry=entry)
    elif request.method == 'POST':
        # Handle the form submission to update the entry
        data = request.form

        # Creates a dictionary to hold the non-empty fields
        update_fields = {}

        # Checks each form field and include non-empty ones in the update
        for field in ['addressLine1', 'addressLine2', 'city', 'stateorprovince', 'zip', 'zipplusfour']:
            value = data.get(field)
            if value is not None:
                update_fields[field] = value

        filter_criteria = {"_id": ObjectId(entry_id)}
        update_operation = {"$set": update_fields}

        # Performs the update operation in the MongoDB collection
        collection.update_one(filter_criteria, update_operation)

        # Redirect to the list of entries 
        return redirect('/entries')


@app.route('/edit_entry/<entryId>', methods=['POST'])
def edit_existing_entry(entryId):
    # Extract updated fields from the request form
    updated_entry = {
        'addressLine1': request.form.get('addressLine1', ''),
        'addressLine2': request.form.get('addressLine2', ''),
        'city': request.form.get('city', ''),
        'stateorprovince': request.form.get('stateorprovince', ''),
        'country': request.form.get('country', ''),
        'zip': request.form.get('zip', ''),
        'zipplusfour': request.form.get('zipplusfour', ''),
    }

    # Update the entry in database using the entryId and updated_entry

    return redirect('/')


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
        entered_zipplusfour = data.get('zipplusfour')      

        print('Received request:', data)

        # Query the MongoDB database looking for a match
        found_match = collection.find_one({
            '$or': [
                {
                    'addressLine1': entered_addresslineone, # Checks if each field entered matches the one in the database with a fuzz ratio of at least 80 percent
                    'fuzzRatio_a_l_one': {'$gt': 80},
                },
                {
                    'addressLine2': entered_addresslinetwo,
                    'fuzzRatio_a_l_two': {'$gt': 80},
                },
                {
                    'city': entered_city,
                    'fuzzRatio_city': {'$gt': 80},
                },
                {
                    'stateorprovince': entered_state,
                },
                {
                    'country': entered_country,
                },
                {
                    'zip': entered_zip,
                    'fuzzRatio_zip': {'$gt': 80},
                },
                {
                    'zipplusfour': entered_zipplusfour,
                    'fuzzRatio_zipplusfour': {'$gt': 80},
                },
            ]
        })

        print('Found Match:', found_match)

        valid_address = found_match is not None


        address_line_one_match = fuzz.ratio(found_match.get('addressLine1'), entered_addresslineone) > 80 # Defines fuzz ratios to be used by partial match variable
        city_match = fuzz.ratio(found_match.get('city'), entered_city) > 80 
        stateorprovince_match = found_match.get('stateorprovince') == entered_state             
        country_match = found_match.get('country') == entered_country
        zip_match = fuzz.ratio(found_match.get('zip'), entered_zip) > 80

        # List of all the required fields
        required_fields = [address_line_one_match,city_match,stateorprovince_match,country_match,zip_match]


        # Counts the number of incorrect fields
        incorrect_count = required_fields.count(False)

        # Criteria for partial match: 1 required field is incorrect
        partial_match = incorrect_count == 1



        perfect_match = ( # Defines criteria for perfect match 
            fuzz.ratio(found_match.get('addressLine1'), entered_addresslineone) > 80 and 
            fuzz.ratio(found_match.get('city'), entered_city) > 80 and
            found_match.get('stateorprovince') == entered_state and
            found_match.get('country') == entered_country and
            fuzz.ratio(found_match.get('zip'), entered_zip) > 80 and
            (
                (found_match.get('addressLine2') and found_match['addressLine2'] == entered_addresslinetwo) or
                (not found_match.get('addressLine2') and not entered_addresslinetwo)  # Both empty
            ) and
            (
                (found_match.get('zipplusfour') and found_match['zipplusfour'] == entered_zipplusfour) or
                (not found_match.get('zipplusfour') and not entered_zipplusfour)  # Both empty
            )
        )
                                                        
        # Creates a response to the POST request
        response = {'validAddress': valid_address,
                    'perfectMatch': perfect_match,
                    'incorrectFields': incorrect_count,
                    'partialMatch': partial_match,
                    'found_match': found_match,
                    'fuzzRatio_a_l_one':fuzz.ratio(found_match.get('addressLine1'), entered_addresslineone),
                    'fuzzRatio_a_l_two':fuzz.ratio(found_match.get('addressLine2'), entered_addresslinetwo),
                    'fuzzRatio_city':fuzz.ratio(found_match.get('city'), entered_city),
                    'fuzzRatio_zip':fuzz.ratio(found_match.get('zip'), entered_zip),
                    'fuzzRatio_zipplusfour':fuzz.ratio(found_match.get('zipplusfour'), entered_zipplusfour),

                    'message': f'Address is valid; match found. Match{found_match}' if valid_address else 'Address is not valid.'} 
        
        
        json_response = dumps(response)    # Converts the response to JSON


        
        print('Sending Response:', response)

        return json_response, 200
    except Exception as error: # Handles Errors with the response
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {error}'}), 500



if __name__ == "__main__": # Instructs app to run when code is executed
    app.run()
