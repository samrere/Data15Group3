import pandas as pd
from datetime import datetime
import pytz
new = pd.read_parquet('linkedin_jobs_Data_Engineer_20241223_224509.parquet')
old = pd.read_json('linkedin_jobs_Data_Engineer_20241209_140037.json')
# Function to convert epoch to UTC datetime string
def convert_epoch_to_datetime(epoch):
    if pd.isna(epoch):
        return None
    return datetime.fromtimestamp(epoch/1000, tz=pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')

# Function to format timestamp to UTC
def format_timestamp(ts):
    if pd.isna(ts):
        return None
    if isinstance(ts, pd.Timestamp):
        return ts.tz_localize('UTC').strftime('%Y-%m-%d %H:%M:%S')
    return convert_epoch_to_datetime(ts)

# 1. First filter new for reposted jobs - create a copy to avoid the warning
new_reposted = new[new['reposted'] == True].copy()

# 2. Extract job_id from job_url in old and ensure correct data type
old['job_id'] = old['job_url'].str.extract(r'view/(\d+)')
old['job_id'] = pd.to_numeric(old['job_id'])
new_reposted['job_id'] = pd.to_numeric(new_reposted['job_id'])

# 3. Find jobs with same company, title, location, AND job_id
exact_matches = pd.merge(
    new_reposted[['job_id', 'company', 'title', 'location', 'posted_time_epoch', 'reposted', 'apply_url']],
    old[['job_id', 'company', 'title', 'location', 'posted_time', 'reposted', 'apply_url']],
    on=['job_id', 'company', 'title', 'location'],
    suffixes=('_new', '_old')
)

# Convert times to readable UTC format
exact_matches['posted_time_new'] = exact_matches['posted_time_epoch'].apply(convert_epoch_to_datetime)
exact_matches['posted_time_old'] = exact_matches['posted_time'].apply(format_timestamp)

# Filter for different posted times
exact_matches = exact_matches[exact_matches['posted_time_new'] != exact_matches['posted_time_old']]

# 4. Find jobs with same company, title, and location but DIFFERENT job_id
title_company_matches = pd.merge(
    new_reposted[['job_id', 'company', 'title', 'location', 'posted_time_epoch', 'reposted', 'apply_url']],
    old[['job_id', 'company', 'title', 'location', 'posted_time', 'reposted', 'apply_url']],
    on=['company', 'title', 'location'],
    suffixes=('_new', '_old')
)

different_job_ids = title_company_matches[
    title_company_matches['job_id_new'] != title_company_matches['job_id_old']
].copy()

# Convert times for different_job_ids to UTC
different_job_ids['posted_time_new'] = different_job_ids['posted_time_epoch'].apply(convert_epoch_to_datetime)
different_job_ids['posted_time_old'] = different_job_ids['posted_time'].apply(format_timestamp)

# Filter for different posted times
different_job_ids = different_job_ids[different_job_ids['posted_time_new'] != different_job_ids['posted_time_old']]

print("Jobs with matching company, title, location, AND job_id but DIFFERENT posting times:")
print(f"Found {len(exact_matches)} matches")
print(exact_matches[['job_id', 'company', 'title', 'location', 'posted_time_new', 'posted_time_old', 'apply_url_new', 'apply_url_old']].head())

print("\nJobs with matching company, title, and location but DIFFERENT job_id and posting times:")
print(f"Found {len(different_job_ids)} matches")
print(different_job_ids[['job_id_new', 'job_id_old', 'company', 'title', 'location', 'posted_time_new', 'posted_time_old', 'apply_url_new', 'apply_url_old']].head())

print("\nSummary:")
print(f"Total reposted jobs in new: {len(new_reposted)}")
print(f"Total matches (same job_id, different times): {len(exact_matches)}")
print(f"Total matches (different job_id, different times): {len(different_job_ids)}")