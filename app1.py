import pandas as pd
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Google Drive File ID
FILE_ID = "1e5X3CPdFT5iqSlQVk1hjTBTx2neQ65m3"
CSV_PATH = "IPO_DETAILS.csv"

df_cached = None

def download_csv_from_drive():
    """Downloads CSV from Google Drive and caches it."""
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

@app.route('/symbol/<symbol>', methods=['GET'])
def get_symbol_details(symbol):
    symbol = symbol.strip().upper()  # Normalize symbol input

    if df_cached is None:
        return jsonify({"error": "Data not available"}), 500

    # Ensure column names match
    temp_df = df_cached.copy()
    temp_df['Symbol'] = temp_df['Symbol'].astype(str).str.strip().str.upper()

    # Filter dataset for the provided symbol
    filtered_data = temp_df[temp_df['Symbol'] == symbol]

    if filtered_data.empty:
        return jsonify({"symbol": symbol, "error": "Symbol not found"}), 404

    # Get the first matching record
    company_record = filtered_data.iloc[0].to_dict()

    # Convert NaN, NaT, or None values to "N/A"
    for key, value in company_record.items():
        if pd.isna(value) or value is None:
            company_record[key] = "N/A"
        elif isinstance(value, (int, float)):
            company_record[key] = str(value) if value != int(value) else str(int(value))

    return jsonify(company_record)


if __name__ == '__main__':
    app.run(debug=True)
