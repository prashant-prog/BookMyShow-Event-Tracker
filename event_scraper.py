# This Project is Created by Prashant Sharma

import os
import sys
import logging
import datetime
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- Configuration ---
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

CITY_URLS = {
    "jaipur": "https://in.bookmyshow.com/explore/events-jaipur",
    "mumbai": "https://in.bookmyshow.com/explore/events-mumbai",
    "delhi": "https://in.bookmyshow.com/explore/events-national-capital-region-ncr",
    "bangalore": "https://in.bookmyshow.com/explore/events-bengaluru",
    "gurgaon": "https://in.bookmyshow.com/explore/events-gurugram"
}

STATUS_UPCOMING = "Upcoming"
STATUS_EXPIRED = "Expired"
STATUS_UNKNOWN = "Unknown"

class EventScraper:
    def __init__(self, city):
        self.city = city.lower()
        self.url = CITY_URLS.get(self.city)
        if not self.url:
            raise ValueError(f"City '{city}' not supported. Supported: {', '.join(CITY_URLS.keys())}")
        self.output_file = f"events_{self.city}.xlsx"

    def fetch_page(self):
        """
        Fetches the HTML content of the page using Playwright.
        """
        logger.info(f"Navigating to {self.url}...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # Increased timeout to 60s for slow networks
                page.goto(self.url, timeout=60000, wait_until="domcontentloaded")
                
                # Wait for at least one anchor with '/events/' in href
                try:
                    page.wait_for_selector('a[href*="/events/"]', timeout=15000)
                except Exception:
                    logger.warning("Timeout waiting for event cards. Page might be empty or structure changed.")

                content = page.content()
                browser.close()
                return content

        except Exception as e:
            logger.error(f"Error extracting with Playwright: {e}")
            return None

    @staticmethod
    def parse_date(date_str):
        """
        Parses BookMyShow date strings. Returns datetime object or None.
        """
        if not date_str or not isinstance(date_str, str):
            return None
            
        clean_str = date_str.split(" onwards")[0].strip()
        current_year = datetime.datetime.now().year
        
        # Formats to try
        date_formats = ["%a, %d %b", "%d %b"]
        
        for fmt in date_formats:
            try:
                # Append year since it's usually missing
                dt = datetime.datetime.strptime(f"{clean_str} {current_year}", f"{fmt} %Y")
                return dt
            except ValueError:
                continue
        return None

    @staticmethod
    def get_event_status(event_date):
        """
        Determines if an event is Upcoming or Expired.
        """
        if not event_date:
            return STATUS_UNKNOWN
        
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return STATUS_UPCOMING if event_date >= today else STATUS_EXPIRED

    def parse_events(self, html_content):
        """
        Parses HTML to extract event details.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []

        # Use CSS selector for efficiency: finds <a> tags with href containing '/events/'
        # Excluding 'explore' links to avoid navigational links
        card_links = soup.select('a[href*="/events/"]')
        
        for card in card_links:
            link = card['href']
            if 'explore' in link:
                continue
                
            full_link = f"https://in.bookmyshow.com{link}" if link.startswith('/') else link
            
            # Extract text safely
            text_items = list(card.stripped_strings)
            if len(text_items) < 3:
                continue

            # Heuristic to detect valid event card structure
            # Normal structure: [Date, Name, Venue, Category, ...]
            # Promoted structure: [Promoted, Date, Name, Venue, Category, ...]
            start_idx = 0
            if "promoted" in text_items[0].lower():
                start_idx = 1
            
            # Ensure we have enough items after skipping 'promoted'
            if len(text_items) < start_idx + 4:
                continue

            raw_date = text_items[start_idx]
            name = text_items[start_idx + 1]
            venue = text_items[start_idx + 2]
            category = text_items[start_idx + 3]

            event_date = self.parse_date(raw_date)
            status = self.get_event_status(event_date)
            
            events.append({
                "Event Name": name,
                "Date": raw_date, # Keeping original string for display
                "ParsedDate": event_date, # Internal use for sorting/status
                "Venue": venue,
                "City": self.city.capitalize(),
                "Category": category,
                "Event URL": full_link,
                "Status": status
            })
            
        return events

    def save_events(self, new_events):
        """
        Save events to Excel, merging with existing data.
        """
        if not new_events:
            logger.warning("No events to save.")
            return

        new_df = pd.DataFrame(new_events)
        
        if os.path.exists(self.output_file):
            try:
                logger.info(f"Found existing file {self.output_file}. Merging data...")
                existing_df = pd.read_excel(self.output_file)
                
                # Combine and deduplicate
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                # Deduplicate by URL, keeping the newest scraped version
                df = combined_df.drop_duplicates(subset=['Event URL'], keep='last')
            except Exception as e:
                logger.error(f"Error reading existing file: {e}. Starting fresh.")
                df = new_df
        else:
            df = new_df

        # Recalculate status for all events (in case dates have passed since last run)
        # We need to re-parse the date string if 'ParsedDate' column was lost in CSV/Excel roundtrip
        # or if we are processing old rows that just have string dates.
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        def refresh_status(row):
            # If we explicitly have a parsed date object (from this run), use it
            if 'ParsedDate' in row and isinstance(row['ParsedDate'], datetime.datetime):
                d = row['ParsedDate']
            else:
                 # Otherwise try to re-parse the string date
                d = self.parse_date(row['Date'])
            
            return self.get_event_status(d)

        df['Status'] = df.apply(refresh_status, axis=1)

        # Remove internal 'ParsedDate' column before saving if we don't want it in the excel
        # Or keep it if we want to debug. User didn't specify, but cleaner to remove or keep.
        # Let's drop it to keep the output file clean as per original format.
        save_df = df.drop(columns=['ParsedDate'], errors='ignore')

        try:
            save_df.to_excel(self.output_file, index=False)
            logger.info(f"Successfully saved {len(save_df)} events to {self.output_file}")
        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")

    def run(self):
        logger.info(f"Starting scrape for {self.city.capitalize()}...")
        html = self.fetch_page()
        if html:
            events = self.parse_events(html)
            logger.info(f"Found {len(events)} raw events.")
            self.save_events(events)
        else:
            logger.error("Failed to retrieve content. Exiting.")

def main():
    city = "jaipur"
    if len(sys.argv) > 1:
        city = sys.argv[1].lower()

    try:
        scraper = EventScraper(city)
        scraper.run()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
