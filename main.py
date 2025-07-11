# real_estate_scraper.py (Final version with corrected listing focus)

import os
import re
import time
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
from collections import Counter
from playwright.sync_api import sync_playwright

# ------------------ Config ------------------
PORTALS = [
    {
        "name": "Properstar",
        "url": "https://www.properstar.es/spain/compra/terreno/marbella",
        "listing_selector": "div[data-testid='listing-card']",  # Focus on divs that wrap listings
        "base_url": "https://www.properstar.es"
    },
]

LICENSE_KEYWORDS = ["licencia", "permit", "ready to build", "project approved", "concedida"]
STUDIO_KEYWORDS = ["architect", "studio", "design", "drawn by"]


# ------------------ Scraper Functions ------------------
def fetch_html_playwright(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)
            html = page.content()
            page.close()
            browser.close()
            return html
    except Exception as e:
        print(f"Error fetching HTML from {url} with Playwright: {e}")
        return None


def extract_listing_links(html, selector, base_url):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select(selector)
        if not cards:
            print(f"[Warning] No listings found with selector: {selector}")
        links = []
        for card in cards:
            a_tag = card.find("a", href=True)
            if a_tag and '/listing/' in a_tag['href']:
                full_url = base_url + a_tag['href']
                links.append(full_url)
        return list(set(links))[:3]
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []


def extract_details(url, portal_name):
    try:
        html = fetch_html_playwright(url)
        soup = BeautifulSoup(html, 'html.parser') if html else None
        if not soup:
            print(f"[Error] Could not parse HTML for {url}")
            return None

        full_text = soup.get_text(separator=' ', strip=True)

        return {
            "listing_url": url,
            "portal": portal_name,
            "title": soup.title.string.strip()[:100] if soup.title else "",
            "price": extract_price(full_text),
            "land_m2": extract_land_size(full_text),
            "location": extract_location(full_text),
            "full_description": full_text[:1000],
            "agency_contact": extract_agency(full_text),
            "license_mention": extract_license(full_text),
            "architecture_studio": extract_studio(full_text),
            "seller_type": extract_seller(full_text),
        }
    except Exception as e:
        print(f"Error extracting details from {url}: {e}")
        return None


# ------------------ Helper Extraction Functions ------------------
def extract_price(text):
    try:
        match = re.search(r"([1-3]\\.?\d{2,3}\\.?\d{0,3})\\s*[\u20ACe]", text)
        return int(match.group(1).replace('.', '')) if match else ""
    except Exception as e:
        print(f"Error extracting price: {e}")
        return ""

def extract_land_size(text):
    try:
        match = re.search(r"(\d{4,})\\s*m²", text)
        return int(match.group(1)) if match else ""
    except Exception as e:
        print(f"Error extracting land size: {e}")
        return ""

def extract_location(text):
    try:
        for loc in ["Marbella", "Estepona", "Benahavís", "Mijas"]:
            if loc.lower() in text.lower():
                return loc
        return "Unknown"
    except Exception as e:
        print(f"Error extracting location: {e}")
        return "Unknown"

def extract_agency(text):
    try:
        match = re.search(r"agency\\s*[:\-]?\\s*([\w\s]+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else "Unknown"
    except Exception as e:
        print(f"Error extracting agency: {e}")
        return "Unknown"

def extract_license(text):
    try:
        found = [kw for kw in LICENSE_KEYWORDS if kw.lower() in text.lower()]
        if found:
            sentences = re.findall(r"[^.]*?(?:%s)[^.]*?\\." % "|".join(found), text, re.IGNORECASE)
            return f"Yes - {'; '.join(sentences[:2])}" if sentences else "Yes"
        return "No"
    except Exception as e:
        print(f"Error extracting license: {e}")
        return "Unknown"

def extract_studio(text):
    try:
        found = [kw for kw in STUDIO_KEYWORDS if kw.lower() in text.lower()]
        if found:
            match = re.search(r"([A-Z][a-z]+\\s(?:Architects|Studio|Design|Group))", text)
            return match.group(1) if match else "Mentioned"
        return "None"
    except Exception as e:
        print(f"Error extracting architecture studio: {e}")
        return "Unknown"

def extract_seller(text):
    try:
        if "direct from owner" in text.lower():
            return "Direct owner"
        if any(kw in text.lower() for kw in ["agency", "real estate"]):
            return "Agency"
        return "Unknown Owner/Studio"
    except Exception as e:
        print(f"Error extracting seller type: {e}")
        return "Unknown"


# ------------------ Debugging Utility ------------------
def analyze_anchor_classes(html_file_path):
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        class_counter = Counter()

        for a in soup.find_all("a"):
            classes = a.get("class")
            if classes:
                class_name = " ".join(classes)
                class_counter[class_name] += 1

        print("\n🔍 Top anchor <a> class names in HTML:")
        for cls, count in class_counter.most_common(10):
            print(f"  - {cls} : {count} occurrences")

    except Exception as e:
        print(f"Error analyzing anchor classes: {e}")


# ------------------ Output Functions ------------------
def save_excel(data, date_str):
    try:
        df = pd.DataFrame(data)
        filename = f"output/marbella_listings_{date_str}.xlsx"
        df.to_excel(filename, index=False)
        print(f"Saved Excel: {filename}")
    except Exception as e:
        print(f"Error saving Excel: {e}")


def save_xml(data, date_str):
    try:
        root = ET.Element("listings")
        for row in data:
            listing = ET.SubElement(root, "listing")
            for key, val in row.items():
                ET.SubElement(listing, key).text = str(val)

        os.makedirs("output/xml", exist_ok=True)
        tree = ET.ElementTree(root)
        xml_path = f"output/xml/marbella_listings_{date_str}.xml"
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        print(f"Saved XML: {xml_path}")
    except Exception as e:
        print(f"Error saving XML: {e}")


# ------------------ Main Script ------------------
def main():
    try:
        os.makedirs("output", exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        all_data = []

        for portal in PORTALS:
            print(f"Scraping {portal['name']}...")
            html = fetch_html_playwright(portal['url'])
            print(f"Fetched {portal['name']} - Length: {len(html) if html else '0'}")
            if not html:
                continue

            debug_path = f"debug_{portal['name'].lower()}.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)

            links = extract_listing_links(html, portal['listing_selector'], portal['base_url'])
            print(f"Found {len(links)} links.")
            for link in links:
                print(f"\tProcessing {link}")
                details = extract_details(link, portal['name'])
                if details:
                    all_data.append(details)
                time.sleep(1)

            analyze_anchor_classes(debug_path)

        if not all_data:
            print("⚠️ No data extracted. Exiting.")
            return

        save_excel(all_data, date_str)
        save_xml(all_data, date_str)
    except Exception as e:
        print(f"Unexpected error during main execution: {e}")


if __name__ == "__main__":
    main()
