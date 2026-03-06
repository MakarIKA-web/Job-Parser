import json
import time
import sys
import io
import re
import os
from google import genai

# 1. Configuring the Windows console for UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 2. Connecting to Gemini with an API Key
client = genai.Client(api_key="")

# 3. Function for request with retry + fallback
def summarize_job(job_posting, prompt, primary_model="gemini-2.5-flash", fallback_model="gemini-2.1", max_retries=5):
    attempt = 0
    while attempt < max_retries:
        try:
            print(f"Attempt {attempt+1} with model {primary_model}")
            response = client.models.generate_content(
                model=primary_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error: {e}")
            attempt += 1
            time.sleep(5)

    print(f"Primary model failed. Trying fallback model {fallback_model}")
    try:
        response = client.models.generate_content(
            model=fallback_model,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Fallback model error: {e}")
        return None

# 4. Creating a new list to store results
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(SCRIPT_DIR, "jobs.json")

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    job_list = json.load(f)

# 5. Creating a new list to store results
all_jobs = []

# 6. Processing of each vacancy
for job_posting in job_list[:10]:  # We will process the first 10 vacancies
    prompt = f"""
You are a job posting assistant. This is required for every job posting:

1. Briefly describe the essence of the work (2-3 sentences).
2. Highlight 5 key requirements for a candidate.
3. Identify 5 key responsibilities.
4. Create 3 specific questions that the candidate can ask the employer.
5. Return everything in JSON with fields: title, company, location, employment_type, summary, key_requirements, key_responsibilities, call_questions, url.

Vacancy:
{job_posting['description']}
"""

    result_text = summarize_job(job_posting, prompt)

    # 7. Parsing the result into JSON
    try:
        summarized_job = json.loads(result_text)
    except (json.JSONDecodeError, TypeError):
        summarized_job = {
            "title": job_posting.get('title', ''),
            "company": job_posting.get('company', ''),
            "location": job_posting.get('location', job_posting.get('city', '')),
            "employment_type": job_posting.get('employment_type', ''),
            "summary": result_text,
            "key_requirements": [],
            "key_responsibilities": [],
            "call_questions": [],
            "url": job_posting.get('url', '')
        }

    # 8. Cleaning summary from ```json ... ``` and nested JSON
    if summarized_job.get("summary"):
        cleaned = re.sub(r"```json\s*|\s*```", "", summarized_job["summary"]).strip()
        try:
            inner = json.loads(cleaned)
            summarized_job["summary"] = inner.get("summary", cleaned)
            for field in ["key_requirements", "key_responsibilities", "call_questions"]:
                if field in inner:
                    summarized_job[field] = inner[field]
        except json.JSONDecodeError:
            summarized_job["summary"] = cleaned

    # Adding the processed vacancy to the general list
    all_jobs.append(summarized_job)

# 9. We save all vacancies in a new file, result.json
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "result.json")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(all_jobs, f, ensure_ascii=False, indent=4)

print(f"Saved {len(all_jobs)} jobs to {OUTPUT_PATH}")
