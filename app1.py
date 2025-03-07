import pandas as pd
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder="templates")
CORS(app)

# Google Drive File ID
FILE_ID = "1Lf-OW2s5weMHLAfP_pENY7I7hVKmjK5h"
CSV_PATH = "IPO_DETAILS.csv"

# Cache the dataset in memory
df_cached = None

def download_csv_from_drive():
    """ Downloads CSV from Google Drive only once and caches it. """
    global df_cached
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(CSV_PATH, "wb") as f:
            f.write(response.content)
            
        df_cached = pd.read_csv(CSV_PATH)
    else:
        df_cached = None

# Load CSV when the app starts
with app.app_context():
    download_csv_from_drive()

@app.route('/')
def index():
    """ Renders the HTML page. """
    return render_template("index.html")

@app.route('/companies', methods=['GET'])
def get_companies():
    """ Returns the list of unique company names. """
    if df_cached is None:
        return jsonify({"error": "Data not available"}), 500
    
    companies = df_cached['Company Name'].dropna().unique().tolist()
    return jsonify({"companies": companies})

@app.route('/company-details', methods=['GET'])
def get_company_data():
    """ Fetches details of a selected company with better null handling. """
    company_name = request.args.get('name', '').strip()
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    
    if df_cached is None:
        return jsonify({"error": "Data not available"}), 500
    
    # Create a temporary lowercase version for filtering
    temp_df = df_cached.copy()
    temp_df['Company Name'] = temp_df['Company Name'].astype(str).str.strip().str.lower()
    
    filtered_data = temp_df[temp_df['Company Name'] == company_name.lower()]
    
    if filtered_data.empty:
        return jsonify({"error": "Company not found"}), 404
    
    # Get the first matching record and handle NaN values
    company_record = filtered_data.iloc[0].to_dict()
    
    # Convert any NaN, NaT, or None values to strings
    for key, value in company_record.items():
        # Check for NaN or None values
        if pd.isna(value) or value is None:
            company_record[key] = "N/A"
        # Convert numeric values to strings with proper formatting
        elif isinstance(value, (int, float)):
            if value == int(value):  # If it's a whole number
                company_record[key] = str(int(value))
            else:
                company_record[key] = str(value)
    
    return jsonify(company_record)
if __name__ == '__main__':
    app.run(debug=True)