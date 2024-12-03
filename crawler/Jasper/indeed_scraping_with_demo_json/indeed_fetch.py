import csv
import json
import re
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime, timedelta

"""
https://github.com/Bunsly/JobSpy
"""

# Scrape job postings from Indeed using specific parameters
# Customize the search term, location, and number of results as needed
jobs = scrape_jobs(
    site_name=["indeed"],  # Job site to scrape (e.g., Indeed)
    search_term="Data",  # Keyword to search for in job titles or descriptions
    location="Australia",  # Location to filter job postings
    results_wanted=50,  # Number of results to retrieve
    hours_old=100,  # Limit results to jobs posted within the last 72 hours
    country_indeed='Australia',  # Specify the country for Indeed search
    verbose=1,  # Logging level: 0 (errors), 1 (warnings), 2 (detailed logs)
)

# Display the number of jobs found
print(f"\nFound {len(jobs)} jobs from Indeed.")

# Exit if no jobs were found
if len(jobs) == 0:
    print("No jobs found. Please adjust your search parameters.")
    exit()

# Print the available columns to identify what data is included in the results
print("Available columns:", jobs.columns.tolist())

# Ensure all required fields are present; fill missing ones with default values
required_columns = [
    'id', 'site', 'job_url', 'job_url_direct', 'title', 'company', 'location',
    'date_posted', 'job_type', 'salary_source', 'interval', 'min_amount',
    'max_amount', 'currency', 'is_remote', 'job_level', 'job_function',
    'listing_type', 'emails', 'description', 'company_industry', 'company_url',
    'company_logo', 'company_url_direct', 'company_addresses',
    'company_num_employees', 'company_revenue', 'company_description'
]

# Add missing columns with a default value of 'N/A'
for column in required_columns:
    if column not in jobs.columns:
        jobs[column] = 'N/A'

# Define a list of commonly sought-after skills to extract from job descriptions
common_skills = [
    'Python', 'SQL', 'AWS', 'ETL', 'Spark', 'Hadoop', 'Kafka',
    'Data Engineering', 'Azure', 'Data Modeling', 'Scala', 'Cloud Computing',
    'Big Data', 'NoSQL', 'Machine Learning', 'Linux', 'Git', 'Docker', 'Kubernetes',
    'C++', 'Java', 'R', 'Tableau', 'Power BI', 'Hive', 'Pig', 'Flume', 'Storm'
]

# Function to extract listed skills from job descriptions
def extract_skills(description):
    found_skills = set()
    if pd.notnull(description):  # Check if description is not null
        for skill in common_skills:
            # Search for exact matches of skills (case-insensitive)
            if re.search(r'\b' + re.escape(skill) + r'\b', str(description), re.IGNORECASE):
                found_skills.add(skill)
    return list(found_skills)

# Apply the skill extraction function to the 'description' column
jobs['skills'] = jobs['description'].apply(extract_skills)

# Parse and standardize the 'date_posted' column into a consistent format
if 'date_posted' in jobs.columns and jobs['date_posted'].notnull().any():
    # Function to convert relative dates (e.g., "2 days ago") into absolute dates
    def parse_relative_date(relative_date_str):
        relative_date_str = str(relative_date_str).lower()
        current_time = datetime.now()

        if 'today' in relative_date_str or 'just posted' in relative_date_str:
            return current_time
        elif 'hour' in relative_date_str:
            hours = re.findall(r'\d+', relative_date_str)
            hours = int(hours[0]) if hours else 1
            return current_time - timedelta(hours=hours)
        elif 'minute' in relative_date_str:
            minutes = re.findall(r'\d+', relative_date_str)
            minutes = int(minutes[0]) if minutes else 1
            return current_time - timedelta(minutes=minutes)
        elif 'day' in relative_date_str:
            days = re.findall(r'\d+', relative_date_str)
            days = int(days[0]) if days else 1
            return current_time - timedelta(days=days)
        elif 'week' in relative_date_str:
            weeks = re.findall(r'\d+', relative_date_str)
            weeks = int(weeks[0]) if weeks else 1
            return current_time - timedelta(weeks=weeks)
        elif 'month' in relative_date_str:
            months = re.findall(r'\d+', relative_date_str)
            months = int(months[0]) if months else 1
            return current_time - timedelta(days=months * 30)
        else:
            return current_time - timedelta(days=30)

    # Apply the parsing function to the 'date_posted' column
    jobs['posted_time'] = jobs['date_posted'].apply(parse_relative_date)
else:
    # If no 'date_posted' data is available, use the current time as a fallback
    current_time = datetime.now()
    jobs['posted_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')

# Convert all datetime columns to strings for JSON serialization
if 'posted_time' in jobs.columns:
    jobs['posted_time'] = pd.to_datetime(jobs['posted_time']).dt.strftime('%Y-%m-%d %H:%M:%S')

# Set an expiration time for job postings (30 days after posting date)
jobs['expire_time'] = pd.to_datetime(jobs['posted_time']) + timedelta(days=30)
jobs['expire_time'] = jobs['expire_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

# Convert all remaining datetime columns to strings to avoid serialization issues
datetime_columns = ['date_posted', 'posted_time', 'expire_time']
for col in datetime_columns:
    if col in jobs.columns:
        jobs[col] = jobs[col].astype(str)

# Convert the jobs DataFrame into a list of dictionaries for JSON export
output_file = 'indeed_jobs_detailed.json'
jobs_list = jobs.to_dict(orient='records')

# Write the data to a JSON file with indentation for readability
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(jobs_list, f, indent=4, ensure_ascii=False)

print(f"\nDetailed job data saved to {output_file}.")
