from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import certifi
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

app = Flask(__name__, template_folder='templates')

# Replace with your MongoDB Atlas URI
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client['MamaNest']  # Database name
patients_collection = db['Patient']  # Collection name

# Helper function to serialize ObjectId
def serialize_patient(patient):
    patient['_id'] = str(patient['_id'])
    return patient

# Home Page
@app.route('/')
def get_patients():
    patients = list(patients_collection.find())
    return render_template("index.html", patients=[serialize_patient(p) for p in patients])

# Create (Add a new patient)
@app.route('/patients', methods=['POST'])
def add_patient():
    data = request.form.to_dict()
    inserted_id = patients_collection.insert_one(data).inserted_id
    new_patient = patients_collection.find_one({"_id": inserted_id})
    return render_template("patient_item.html", patient=serialize_patient(new_patient))

# Read (Get all patients - SSR)
@app.route('/patients', methods=['GET'])
def get_patients_page():
    patients = list(patients_collection.find())
    return render_template("patients.html", patients=[serialize_patient(p) for p in patients])

# Read (Get a single patient by ID)
@app.route('/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
    if patient:
        return render_template("patient_details.html", patient=serialize_patient(patient))
    return "Patient not found", 404

# Update (Modify a patient’s details)
@app.route('/patients/<patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.form.to_dict()
    result = patients_collection.update_one({"_id": ObjectId(patient_id)}, {"$set": data})
    if result.matched_count:
        updated_patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
        return render_template("patient_item.html", patient=serialize_patient(updated_patient))
    return "Patient not found", 404

# Delete (Remove a patient record)
@app.route('/patients/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    result = patients_collection.delete_one({"_id": ObjectId(patient_id)})
    if result.deleted_count:
        return "<script>document.getElementById('patient-details').innerHTML = '';</script>", 200
    return "Patient not found", 404

# Add a heart rate entry
@app.route('/patients/<patient_id>/heart_rate', methods=['POST'])
def add_heart_rate(patient_id):
    data = request.form.to_dict()
    data['DateObserved'] = data.get('DateObserved', '')  # Ensure DateObserved field is included
    result = patients_collection.update_one({"_id": ObjectId(patient_id)}, {"$push": {"HeartRates": data}})
    if result.matched_count:
        updated_patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
        return render_template("patient_details.html", patient=serialize_patient(updated_patient))
    return "Patient not found", 404

# Add a medication entry
@app.route('/patients/<patient_id>/medications', methods=['POST'])
def add_medication(patient_id):
    data = request.form.to_dict()
    result = patients_collection.update_one({"_id": ObjectId(patient_id)}, {"$push": {"Medications": data}})
    if result.matched_count:
        updated_patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
        return render_template("patient_details.html", patient=serialize_patient(updated_patient))
    return "Patient not found", 404

if __name__ == '__main__':
    app.run(debug=True)
