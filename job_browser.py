import json
from datetime import datetime
import re

# ==========================
# Deadline parsing function
# ==========================
def parse_deadline(text):
    match = re.search(r'(\d{1,2})\.\s*(\w+)', text)
    if not match:
        return datetime.max
    day = int(match.group(1))
    month_str = match.group(2).lower()
    months = {
        "januar": 1, "februar": 2, "mars": 3, "april": 4, "mai": 5,
        "juni": 6, "juli": 7, "august": 8, "september": 9,
        "oktober": 10, "november": 11, "desember": 12
    }
    month = months.get(month_str, 1)
    return datetime(datetime.now().year, month, day)

# ==========================
# Filtering with AND/OR support
# ==========================
def filter_jobs_advanced(jobs, cities=None, employment_types=None, keywords=None, logic='AND'):
    filtered = []
    for job in jobs:
        matches = []
        if cities:
            city_match = any(city.lower() in job.get("city", "").lower() for city in cities)
            matches.append(city_match)
        if employment_types:
            emp_match = any(emp.lower() in job.get("employment_type", "").lower() for emp in employment_types)
            matches.append(emp_match)
        if keywords:
            kw_match = any(kw.lower() in job.get("title", "").lower() for kw in keywords)
            matches.append(kw_match)
        if not matches:
            include = True
        elif logic.upper() == 'AND':
            include = all(matches)
        else:
            include = any(matches)
        if include:
            filtered.append(job)
    return filtered

# ==========================
# Sorting
# ==========================
def sort_jobs(jobs, sort_by='deadline'):
    if sort_by == 'deadline':
        jobs.sort(key=lambda x: parse_deadline(x.get("deadline", "")))
    elif sort_by == 'title':
        jobs.sort(key=lambda x: x.get("title", "").lower())
    elif sort_by == 'company':
        jobs.sort(key=lambda x: x.get("company", "").lower())
    return jobs

# ==========================
# Reading JSON
# ==========================
file_path = r""
with open(file_path, "r", encoding="utf-8-sig") as f:
    jobs = json.load(f)

# ==========================
# Tips
# ==========================
all_cities = sorted(set(job.get("city","-") for job in jobs if job.get("city")))
all_employment = sorted(set(job.get("employment_type","-") for job in jobs if job.get("employment_type")))
all_keywords = sorted(set(job.get("title","-") for job in jobs if job.get("title")))

print("\nAvailable cities:", ", ".join(all_cities))
print("Available employment types:", ", ".join(all_employment))
print("Some job title keywords:", ", ".join([k.split()[0] for k in all_keywords[:20]]))

# ==========================
# User input of filters
# ==========================
cities_input = input("\nFilter by cities (comma separated, or leave empty): ").strip()
cities = [c.strip() for c in cities_input.split(",")] if cities_input else None

employment_input = input("Filter by employment types (comma separated, or leave empty): ").strip()
employment_types = [e.strip() for e in employment_input.split(",")] if employment_input else None

keywords_input = input("Enter keywords for job title (comma separated, or leave empty): ").strip()
keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else None

logic_input = input("Filter logic ('AND' or 'OR', default AND): ").strip().upper() or 'AND'

print("\nChoose sorting field:")
print("1 - deadline")
print("2 - title")
print("3 - company")
sort_choice = input("Enter number (1/2/3): ").strip()
sort_map = {'1': 'deadline', '2': 'title', '3': 'company'}
sort_by = sort_map.get(sort_choice, 'deadline')

top_n_input = input("How many jobs to display? (1/5/10/25): ").strip()
try:
    top_n = int(top_n_input)
except ValueError:
    top_n = 10

# ==========================
# Filtering and sorting
# ==========================
filtered_jobs = filter_jobs_advanced(
    jobs,
    cities=cities,
    employment_types=employment_types,
    keywords=keywords,
    logic=logic_input
)

sorted_jobs = sort_jobs(filtered_jobs, sort_by=sort_by)
result = sorted_jobs[:top_n] if top_n else sorted_jobs

# ==========================
# Output of results
# ==========================
print(f"\nTop {len(result)} jobs sorted by {sort_by}:\n")
for i, job in enumerate(result, 1):
    title = job.get('title', '-')
    company = job.get('company', '-')
    city = job.get('city', '-')
    deadline = job.get('deadline') or "-"
    print(f"{i}. {title} - {company} - {city} - {deadline}")

# ==========================
# Possibility to get a link to a vacancy by number
# ==========================
while True:
    choice = input("\nEnter job number to see application link (or 'exit' to quit): ").strip()
    if choice.lower() == 'exit':
        break
    try:
        num = int(choice)
        if 1 <= num <= len(result):
            selected_job = result[num - 1]
            print(f"Application link: {selected_job.get('url', 'No URL available')}")
        else:
            print(f"Please enter a number between 1 and {len(result)}")
    except ValueError:
        print("Invalid input. Enter a number or 'exit'.")
