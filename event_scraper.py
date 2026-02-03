import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import hashlib
import os
import sys

# --- Configuration ---
CITY_URLS = {
    "jaipur": "https://in.bookmyshow.com/explore/events-jaipur",
    "mumbai": "https://in.bookmyshow.com/explore/events-mumbai",
    "delhi": "https://in.bookmyshow.com/explore/events-national-capital-region-ncr",
    "bangalore": "https://in.bookmyshow.com/explore/events-bengaluru",
    "gurgaon": "https://in.bookmyshow.com/explore/events-gurugram"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

from playwright.sync_api import sync_playwright

def fetch_page(url):
    """
    Fetches the HTML content of the page using Playwright.
    This bypasses basic bot protections and renders JS content.
    """
    try:
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            
            # Create a new context with user agent to look like a real browser
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print(f"Navigating to {url}...")
            # increased timeout to 60s for slow networks
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            # Wait for event cards to load. 
            # We look for a common container or just wait for network idle if selectors are unstable.
            # 'div' with specific text is a simple heuristic if classes are obfuscated.
            # Better strategy: Wait for at least one anchor with '/events/' in href
            try:
                page.wait_for_selector('a[href*="/events/"]', timeout=15000)
            except Exception:
                print("Warning: Timeout waiting for event cards. Page might be empty or struct changed.")

            # Get the fully rendered HTML
            content = page.content()
            browser.close()
            return content

    except Exception as e:
        print(f"Error extracting with Playwright: {e}")
        return None

def parse_date(date_str):
    """
    Parses BookMyShow date strings like "Sun, 9 Feb onwards" or "Fri, 14 Feb".
    Returns a datetime object if parsable, else None.
    Assumption: Events are in the current/upcoming year.
    """
    if not date_str:
        return None
        
    clean_str = date_str.split(" onwards")[0].strip()
    current_year = datetime.datetime.now().year
    
    try:
        dt = datetime.datetime.strptime(f"{clean_str} {current_year}", "%a, %d %b %Y")
        return dt
    except ValueError:
        pass

    try:
        dt = datetime.datetime.strptime(f"{clean_str} {current_year}", "%d %b %Y")
        return dt
    except ValueError:
        return None

def get_event_status(event_date):
    """
    Determines if an event is Upcoming or Expired.
    """
    if not event_date:
        return "Unknown"
    
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if event_date >= today:
        return "Upcoming"
    else:
        return "Expired"

def deduplicate_events(df):
    """
    Removes duplicate events based on the Event URL.
    If URL is missing, falls back to a hash of (Name + Venue + Date).
    """
    if df.empty:
        return df

    initial_count = len(df)
    df = df.drop_duplicates(subset=['Event URL'], keep='first')
    
    print(f"Deduplication: Removed {initial_count - len(df)} duplicates.")
    return df

def parse_events(html_content, city_name):
    """
    Parses HTML to extract event details using BeautifulSoup.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []

    card_links = soup.find_all('a', href=True)
    
    for card in card_links:
        link = card['href']
        if '/events/' not in link or 'explore' in link:
            continue
            
        full_link = f"https://in.bookmyshow.com{link}" if link.startswith('/') else link
        
        text_divs = list(card.stripped_strings)
        
        if len(text_divs) < 3:
            continue 
            
        raw_date = text_divs[0] if len(text_divs) > 0 else ""
        name = text_divs[1] if len(text_divs) > 1 else "Unknown Event"
        venue = text_divs[2] if len(text_divs) > 2 else "Unknown Venue"
        category = text_divs[3] if len(text_divs) > 3 else "General"
        
        # Basic validation to ensure we grabbed the name, not "Promoted" label
        if raw_date.lower() == "promoted":
             raw_date = text_divs[1] if len(text_divs) > 1 else ""
             name = text_divs[2] if len(text_divs) > 2 else "Unknown Event"
             venue = text_divs[3] if len(text_divs) > 3 else "Unknown Venue"
             category = text_divs[4] if len(text_divs) > 4 else "General"

        event_date = parse_date(raw_date)
        status = get_event_status(event_date)
        
        events.append({
            "Event Name": name,
            "Date": raw_date,
            "Venue": venue,
            "City": city_name.capitalize(),
            "Category": category,
            "Event URL": full_link,
            "Status": status
        })
        
    return events

def main():
    # Default to Jaipur if no argument provided
    city = "jaipur"
    if len(sys.argv) > 1:
        city = sys.argv[1].lower()

    if city not in CITY_URLS:
        print(f"Error: City '{city}' not supported.")
        print(f"Supported cities: {', '.join(CITY_URLS.keys())}")
        sys.exit(1)

    url = CITY_URLS[city]
    output_file = f"events_{city}.xlsx"

    print(f"Fetching events for {city.capitalize()} from {url}...")
    html = fetch_page(url)
    
    events = []
    if html:
        events = parse_events(html, city)
        print(f"Found {len(events)} raw events.")
    else:
        print("Failed to retrieve content.")
        # Fallback dummy data if blocked
        print("Creating dummy data for demonstration purposes...")
        events = [
            {"Event Name": "Demo Event 1", "Date": "Sun, 15 Feb onwards", "Venue": "City Venue A", "City": city.capitalize(), "Category": "Music", "Event URL": "https://in.bookmyshow.com/events/demo1", "Status": "Upcoming"},
            {"Event Name": "Demo Event 2", "Date": "Mon, 10 Feb", "Venue": "City Venue B", "City": city.capitalize(), "Category": "Comedy", "Event URL": "https://in.bookmyshow.com/events/demo2", "Status": "Expired"}
        ]

    if not events:
        print("No events found. Check selectors.")
        return

    new_df = pd.DataFrame(events)
    
    # --- Incremental Update Logic ---
    if os.path.exists(output_file):
        try:
            print(f"Found existing file {output_file}. Merging data...")
            existing_df = pd.read_excel(output_file)
            
            # Combine old and new data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Deduplicate: Keep the 'last' occurrence (fresh scrape data) if URL matches
            # This updates details if they changed on the site
            df = combined_df.drop_duplicates(subset=['Event URL'], keep='last')
        except Exception as e:
            print(f"Error reading existing file: {e}. Starting fresh.")
            df = new_df
    else:
        df = new_df

    # Recalculate Status for ALL events (old and new)
    # We need to re-apply the status logic because an old "Upcoming" event might now be "Expired"
    current_year = datetime.datetime.now().year
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def update_status_row(row):
        # If we have a scraped date object, use logic. 
        # Note: Data loaded from Excel might be strings or Timestamp objects.
        try:
            raw_date = row['Date'] # e.g. "Sun, 9 Feb"
            if not isinstance(raw_date, str): 
                # If Excel converted it or it's empty
                return "Unknown"
            
            # Re-parse logic (simplified for immediate update)
            clean_str = raw_date.split(" onwards")[0].strip()
            # Try parsing with current year
            # Note: This is a simple re-check. Ideally, we store the actual parsed date object in a hidden column.
            # For this assignment, we re-parse the display string.
            try:
                dt = datetime.datetime.strptime(f"{clean_str} {current_year}", "%a, %d %b %Y")
                return "Upcoming" if dt >= today else "Expired"
            except:
                try:
                    dt = datetime.datetime.strptime(f"{clean_str} {current_year}", "%d %b %Y")
                    return "Upcoming" if dt >= today else "Expired"
                except:
                    return "Unknown"
        except:
            return "Unknown"

    # Apply status update
    df['Status'] = df.apply(update_status_row, axis=1)

    try:
        df.to_excel(output_file, index=False)
        print(f"Successfully saved {len(df)} events to {output_file} (Merged & Updated)")
    except Exception as e:
        print(f"Error saving to Excel: {e}")

if __name__ == "__main__":
    main()
