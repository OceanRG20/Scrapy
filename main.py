import time
import os
import pandas as pd
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# ------------------ CONFIG ------------------
URL = "https://www.properstar.es/espana/castilla-y-leon/comprar/piso-casa"

# ------------------ LAUNCH HEADLESS BROWSER ------------------
def start_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    return webdriver.Chrome(options=options)

# ------------------ SCRAPE PROPERTY LISTINGS ------------------
def scrape_properstar_listings():
    driver = start_driver()
    driver.get(URL)
    time.sleep(6)  # Wait for JavaScript to render

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Save HTML for debug
    os.makedirs("output", exist_ok=True)
    with open("output/raw_soup.txt", "w", encoding="utf-8") as f:
        f.write(str(soup))

    listings = []
    articles = soup.select("article.item-adaptive.card-extended.vendor-hidden")

    for article in articles:
        # Title and link
        title_tag = article.select_one("a.link.listing-title.stretched-link")
        title = title_tag.text.strip() if title_tag else "N/A"
        url = "https://www.properstar.es" + title_tag["href"] if title_tag else "N/A"

        # Price
        price_tag = article.select_one("div.listing-price-main span")
        price = price_tag.text.strip() if price_tag else "N/A"

        # Location
        location_tag = article.select_one("div.item-location")
        location = location_tag.get("title") if location_tag else "N/A"

        # Highlights / Description
        highlight_tag = article.select_one("div.item-highlights")
        description = highlight_tag.text.strip() if highlight_tag else "N/A"

        # First image
        image_tag = article.select_one("div.image-gallery-slide img")
        image = (
            image_tag.get("src") or image_tag.get("data-src")
            if image_tag else "N/A"
        )

        # Append entry
        listings.append({
            "Title": title,
            "Listing URL": url,
            "Price": price,
            "Location": location,
            "Description": description,
            "Image URL": image
        })

    return listings

# ------------------ SAVE TO EXCEL ------------------
def save_to_excel(data, path):
    df = pd.DataFrame(data)
    df.to_excel(path, index=False)
    print(f"📦 Excel saved to {path}")

# ------------------ SAVE TO XML ------------------
def save_to_xml(data, path):
    root = ET.Element("listings")
    for row in data:
        listing = ET.SubElement(root, "listing")
        for key, value in row.items():
            tag = ET.SubElement(listing, key.replace(" ", "_").lower())
            tag.text = str(value)
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print(f"📦 XML saved to {path}")

# ------------------ MAIN ENTRY POINT ------------------
def main():
    listings = scrape_properstar_listings()
    os.makedirs("output", exist_ok=True)
    save_to_excel(listings, "output/castilla_y_leon_listings.xlsx")
    save_to_xml(listings, "output/castilla_y_leon_listings.xml")

if __name__ == "__main__":
    main()
