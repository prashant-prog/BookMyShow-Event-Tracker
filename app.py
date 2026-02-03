#This Project is Created by Prashant Sharma
from flask import Flask, render_template, jsonify, request
import subprocess
import os
import sys

# Initialize Flask app
# We use standard folder structure: templates/ for HTML, static/ for CSS/JS
app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def home():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/run-scraper', methods=['POST'])
def run_scraper():
    """
    Endpoint to trigger the event scraper script.
    Expects JSON body: { "city": "city_name" }
    """
    try:
        # Get city from request, default to 'jaipur' if not provided
        data = request.get_json() or {}
        city = data.get('city', 'jaipur').lower()
        
        # Validate city to prevent arbitrary command execution or weird filenames
        allowed_cities = ['jaipur', 'mumbai', 'delhi', 'bangalore', 'gurgaon']
        if city not in allowed_cities:
             return jsonify({
                "status": "error", 
                "message": f"Invalid city selected: {city}"
            }), 400

        # Run the existing event_scraper.py script as a subprocess with the city argument
        result = subprocess.run(
            [sys.executable, 'event_scraper.py', city],
            capture_output=True,
            text=True,
            check=True
        )
        
        output_file = f"events_{city}.xlsx"
        
        # Check if the Excel file was actually created/updated
        if os.path.exists(output_file):
            return jsonify({
                "status": "success", 
                "message": f"Events for {city.capitalize()} successfully fetched!",
                "details": result.stdout
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Script ran but no output file found."
            }), 500

    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error", 
            "message": f"Scraper script failed: {e.stderr}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
