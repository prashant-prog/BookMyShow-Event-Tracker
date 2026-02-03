# Event Discovery & Tracking Tool - Partial Build Explanation

## 1. Data Extraction & Strategy
**Approach:** 
We use **Playwright** (headless Chromium) to fetch the HTML content.
- **Why Playwright?** BookMyShow employs strong bot detection (403 Forbidden on standard `requests`). Playwright renders the page like a real browser, executing JavaScript and bypassing these blocks.
- **Selectors:** We target the event card containers `a[href*='/events/']`.
- **Performance:** While slower than `requests`, it ensures reliable data retrieval from protected pages.

## 2. City Selection Logic
**Current Implementation:**
- We support **Jaipur, Mumbai, Delhi, Bangalore, and Gurgaon**.
- The backend accepts a city argument (e.g., `python event_scraper.py mumbai`) or a JSON payload via the Flask API.
- URLs are mapped in a configuration dictionary: `{'jaipur': '.../events-jaipur', ...}`.

## 3. Data Structure & Excel
The data is structured as a list of dictionaries, then converted to a **Pandas DataFrame** for easy manipulation.
**Excel Columns:**
- `Event Name`: Title of the event.
- `Date`: Raw date string (cleaned).
- `Venue`: Location of the event.
- `City`: 'Jaipur'.
- `Category`: e.g., Comedy, Music.
- `Event URL`: Unique link to the event.
- `Status`: Upcoming vs. Expired.

## 4. Deduplication Strategy
Duplicate events are a common issue in scraping (e.g., pagination overlap or promoted slots).
**Logic:**
1.  **Primary Key:** The `Event URL` is unique for every event instance (e.g., `/events/sunburn-arena/ET00123...`). We drop duplicates based on this column.
2.  **Fallback:** If URLs were dynamic, we would create a hash of `(Event Name + Date + Venue)` to identify uniqueness.

## 5. Expiry Handling
**Status Determination:**
- We parse the date string (e.g., "Sun, 9 Feb") into a Python `datetime` object.
- **Logic:** `if event_date < today: Status = 'Expired' else: 'Upcoming'`.
- **Note:** BookMyShow mostly displays upcoming events on the explore page, so this logic is forward-looking for when we store historic data over time.

## 6. Automation & Scalability (Future Scope)
To turn this into a production system:
- **Scheduler:** Use a `cron` job (Linux) or Windows Task Scheduler to run the script daily at 8:00 AM.
  - `0 8 * * * /usr/bin/python3 /path/to/script.py`
- **Reliability:** Implement retry logic (exponential backoff) for network failures.
- **Storage:** Move from Excel to a lightweight database like **SQLite** or **PostgreSQL** to query trends over time without loading massive files.
- **Proxies:** Use a proxy rotation service (e.g., BrightData) to prevent IP bans.

**Assumptions:**
- The HTML structure of the event cards remains relatively consistent.
- Events listed without a specific year are assumed to be in the current/next rolling year.
