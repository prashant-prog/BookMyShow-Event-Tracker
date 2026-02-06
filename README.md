# Event Discovery & Tracking Tool

A full-stack Python application that scrapes live event data from BookMyShow using Playwright, tracks event history incrementally, and provides a simple web interface for multi-city support.

## 🚀 Features

- **Live Data Scraping**: Uses **Playwright** (Headless Chromium) to bypass bot protections (403 Forbidden) and render dynamic JavaScript content.
- **Multi-City Support**: Built-in support for **Jaipur, Mumbai, Delhi, Bangalore, and Gurgaon**.
- **Incremental Updates**: Merges new data with existing records. keeps track of history and marks past events as 'Expired' rather than deleting them.
- **Excel Export**: data is saved to clean, city-specific Excel files (e.g., `events_mumbai.xlsx`).
- **Web Interface**: A lightweight Flask + Vanilla JS frontend for easy interaction.

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip

### 1. Clone & Setup
Navigate to the project directory:
```bash
cd /path/to/project
```

### 2. Create Virtual Environment
It is recommended to use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
This is critical for the scraper to work:
```bash
playwright install chromium
```

## 🏃 Usage

### Option A: Run the Web App (Recommended)
Start the Flask server:
```bash
python3 app.py
```
- Open your browser and go to `http://localhost:5000`.
- Select a city from the dropdown.
- Click **"Fetch / Update Events"**.
- The backend will scrape the data and create/update the `events_{city}.xlsx` file in the project folder.

### Option B: Run Scraper via Command Line
You can run the scraper directly for a specific city:
```bash
# Usage: python event_scraper.py [city_name]
python event_scraper.py mumbai
```

## 📂 Project Structure

```
├── app.py                 # Flask backend API & Server
├── event_scraper.py       # Main scraping logic (Playwright + Pandas)
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Frontend HTML
├── static/
│   ├── script.js          # Frontend Logic (Fetch API)
│   └── style.css          # Styling
└── events_*.xlsx          # Generated output files (ignored in git)
```

## ⚙️ Configuration & Automation

### Adding New Cities
To add a new city, edit the `CITY_URLS` dictionary in `event_scraper.py`:
```python
CITY_URLS = {
    "jaipur": "https://in.bookmyshow.com/explore/events-jaipur",
    "newcity": "https://in.bookmyshow.com/explore/events-newcity",
    # ...
}
```
And update `templates/index.html` to include the new option in the dropdown.

### Scheduling (Cron)
To automate this script to run daily at 8:00 AM:
```bash
0 8 * * * /path/to/your/venv/bin/python /path/to/project/event_scraper.py jaipur
```

## ❓ Troubleshooting

### Playwright Browser Issues
If you see an error like `Executable doesn't exist at ...`, run:
```bash
playwright install chromium
```

### Timeout Errors
If the scraper times out:
1.  Check your internet connection.
2.  The script waits up to 60 seconds. You can increase the `timeout` in `event_scraper.py` if needed.
3.  Ensure `headless=True` in `event_scraper.py` (default).

## 📝 Technologies Used
- **Python**: Core logic.
- **Playwright**: Browser automation & scraping.
- **Pandas**: Data manipulation & Excel export.
- **Flask**: Lightweight web server.
- **HTML/CSS/JS**: Simple, responsive frontend.


## This Project is Created By Prashant Sharma
