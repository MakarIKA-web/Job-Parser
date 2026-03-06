from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import json
import os
import re
from dataclasses import dataclass, asdict

BASE_URL = "https://arbeidsplassen.nav.no"

START_URL = (
    "https://arbeidsplassen.nav.no/stillinger?"
    "workLanguage=Norsk&v=5&"
    "education=Videreg%C3%A5ende&"
    "education=Ingen+krav&"
    "county=TELEMARK&"
    "municipal=TELEMARK.PORSGRUNN&"
    "municipal=TELEMARK.SKIEN&"
    "municipal=TELEMARK.BAMBLE&"
    "pageCount=100"
)

def get_soup(url):
    r = requests.get(url)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

# -------------------------------------------------
# STEP 1 — GET JOB LINKS USING PLAYWRIGHT
# -------------------------------------------------

def collect_links():
    job_links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Opening main page...")
        page.goto(START_URL)
        page.wait_for_timeout(5000)

        # Scroll down (if lazy loading)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)

        articles = page.query_selector_all("article a[href*='/stillinger/stilling/']")

        for a in articles:
            href = a.get_attribute("href")
            if href:
                full_url = urljoin(BASE_URL, href)
                if full_url not in job_links:
                    job_links.append(full_url)

        browser.close()

    print(f"Collected {len(job_links)} links")
    return job_links

# -------------------------------------------------
# DTO for the vacancy
# -------------------------------------------------
@dataclass
class JobDTO:
    job_id: str
    title: str
    company: str
    location_full: str
    street: str
    postal_code: str
    city: str
    employment_type: str
    work_time: str
    language: str
    positions: str
    workplace: str
    deadline: str
    apply_link: str
    description: str
    url: str

# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------

def extract_text(el):
    return el.get_text(strip=True) if el else ""

def get_dd(soup, label):
    for dt in soup.select("dl.ad-description-list dt"):
        if label.lower() in dt.get_text(strip=True).lower():
            dd = dt.find_next("dd")
            return extract_text(dd)
    return ""

# -------------------------------------------------
# STEP 2 — SCRAPE EACH JOB WITH BEAUTIFULSOUP
# -------------------------------------------------

def scrape_job(url):
    soup = get_soup(url)

    title = extract_text(soup.select_one("h1.aksel-heading--xlarge"))
    company = extract_text(
        soup.select_one("section p.aksel-body-long.aksel-typo--semibold")
    )

    # Address
    address_blocks = soup.select("section p.aksel-body-long.aksel-typo--semibold")
    location_full = address_blocks[1].get_text(strip=True) if len(address_blocks) > 1 else ""

    street = ""
    postal_code = ""
    city = ""

    if location_full and "," in location_full:
        parts = location_full.split(",")
        street = parts[0].strip()

        if len(parts) > 1:
            match = re.search(r"(\d{4})\s+(.*)", parts[1])
            if match:
                postal_code = match.group(1)
                city = match.group(2)

    employment_type = get_dd(soup, "Type ansettelse")
    work_language = get_dd(soup, "Arbeidsspråk")
    positions = get_dd(soup, "Antall stillinger")
    workplace = get_dd(soup, "Arbeidssted")
    work_time = get_dd(soup, "Arbeidstid")

    description_block = soup.select_one("div.arb-rich-text.job-posting-text")
    description = ""
    if description_block:
        description = description_block.get_text("\n", strip=True)

    deadline = ""
    deadline_block = soup.find(string=lambda s: s and "Søk senest" in s)
    if deadline_block:
        deadline = deadline_block.strip()

    apply_link = ""
    apply_btn = soup.select_one("a.aksel-button[href*='apply']")
    if apply_btn:
        apply_link = apply_btn.get("href", "")

    job_id = url.rstrip("/").split("/")[-1]

    # ← replaced by DTO
    return JobDTO(
        job_id=job_id or "",
        title=title or "",
        company=company or "",
        location_full=location_full or "",
        street=street or "",
        postal_code=postal_code or "",
        city=city or "",
        employment_type=employment_type or "",
        work_time=work_time or "",
        language=work_language or "",
        positions=positions or "",
        workplace=workplace or "",
        deadline=deadline or "",
        apply_link=apply_link or "",
        description=description or "",
        url=url
    )

# -------------------------------------------------
# MAIN
# -------------------------------------------------

if __name__ == "__main__":

    job_links = collect_links()

    all_jobs = []
    for link in job_links:
        print("Scraping:", link)
        try:
            job_dto = scrape_job(link)
            all_jobs.append(asdict(job_dto))  # ← serializing a DTO into a dictionary for JSON
        except Exception as e:
            print("Error:", e)

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_PATH = os.path.join(SCRIPT_DIR, "jobs.json")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=4)

    print(f"Saved {len(all_jobs)} jobs to {OUTPUT_PATH}")
