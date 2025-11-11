import requests
import json
import time
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Securely get the token from .env
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# MAXIMUM number of items to fetch for each task (for API limits)
# Set to None to fetch all data (can take hours/days).
MAX_ITEMS_PER_TASK = None 
# -------------------------------------

# Project Information
REPO_OWNER = "scikit-learn"
REPO_NAME = "scikit-learn"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
ITEMS_PER_PAGE = 100 # Max value for API is 100

# Headers for authentication with Token
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def print_status(message, is_header=False):
    """Helper function for formatted printing"""
    if is_header:
        print("\n" + "="*60)
        print(f" {message}")
        print("="*60)
    else:
        print(f"[INFO] {message}")

def save_to_jsonl(filename, data_list):
    """Saves a list of data to a .jsonl (JSON Lines) file."""
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print_status(f"Successfully saved {len(data_list)} items to {filename}.")

def fetch_paginated_data(url, params, max_items):
    """
    Fetches paginated data from the GitHub API.
    Continues until 'max_items' limit is reached or data runs out.
    Waits for 1 hour if API rate limit is hit.
    """
    all_items = []
    params['per_page'] = ITEMS_PER_PAGE
    page = 1
    
    while True:
        if max_items is not None and len(all_items) >= max_items:
            print_status(f"Limit ({max_items}) exceeded. Stopping data fetch.")
            break
            
        params['page'] = page
        try:
            # Check for token existence before each request
            if not GITHUB_TOKEN:
                print("[ERROR] GITHUB_TOKEN not found. Stopping script.")
                return None # Safely stop the function if no token

            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                print_status("All data fetched (last page).")
                break
                
            all_items.extend(data)
            
            print_status(f"Page {page} fetched. Total {len(all_items)} items retrieved...")
            
            if 'next' not in response.links:
                print_status("All data fetched (no 'next' link header).")
                break
                
            page += 1
            # A respectful pause to avoid hitting API Rate Limits
            time.sleep(1) # Wait 1 second between pages

        except requests.exceptions.RequestException as e:
            error_message = str(e).lower()
            print(f"[ERROR] API request failed (Page {page}): {e}")
            
            if "bad credentials" in error_message:
                print("[ERROR] GITHUB_TOKEN is invalid or has expired. Please check.")
                break # Don't continue with a bad token
            
            if "rate limit exceeded" in error_message:
                print("[ERROR] API rate limit exceeded. Script is pausing for 1 hour (3601 seconds)...")
                time.sleep(3601) # Wait 1 hour + 1 second
                print("[INFO] Wait finished, retrying same page ({page})...")
                continue # Continue the loop to retry the same page
            
            # For other errors, break the loop
            break
            
    if max_items is not None:
        return all_items[:max_items] # Apply the limit exactly
    return all_items

# --- Task-Specific Data Fetching Functions ---

def task_1_code_search(max_items):
    """
    Task 1: Code Search (Natural Language Query -> Code)
    Strategy: Get 'issue' titles as 'query' and 'body' as 'code/description'.
    """
    print_status("Task 1: Collecting Code Search (Issues) Data...", is_header=True)
    url = f"{BASE_URL}/issues"
    params = {'state': 'all', 'sort': 'updated', 'direction': 'desc'}
    issues = fetch_paginated_data(url, params, max_items)
    if issues is None: return # Stop if token failed
    
    dataset = []
    for issue in issues:
        # Only get issues that are not Pull Requests
        if 'pull_request' not in issue:
            dataset.append({
                'task': 'code_search', 'id': issue['id'], 'query': issue['title'], # Natural Language Query
                'body': issue['body'], 'url': issue['html_url'] # Potential Code/Description
            })
    save_to_jsonl('task_1_code_search.jsonl', dataset)

def task_3_bug_classification(max_items):
    """
    Task 3: Bug Classification (Code Change -> Is it a bug?)
    Strategy: Fetch Pull Requests (PRs) and their 'labels'.
    'diff_url' will be used later to download the code change.
    """
    print_status("Task 3: Collecting Bug Classification (PRs) Data...", is_header=True)
    url = f"{BASE_URL}/pulls"
    params = {'state': 'all', 'sort': 'updated', 'direction': 'desc'}
    pull_requests = fetch_paginated_data(url, params, max_items)
    if pull_requests is None: return # Stop if token failed

    dataset = []
    for pr in pull_requests:
        dataset.append({
            'task': 'bug_classification', 'id': pr['id'], 'pr_number': pr['number'],
            'title': pr['title'], 'labels': [label['name'] for label in pr['labels']], # Classification label
            'diff_url': pr['diff_url'], 'state': pr['state'] # Code diff (to be fetched later)
        })
    save_to_jsonl('task_3_bug_classification.jsonl', dataset)

def task_2_and_4_commits(max_items):
    """
    Task 2 & 4: Code Repair (Buggy -> Fixed) and Commit Message Generation
    Strategy: Fetch all commits.
    - Task 4 (Commit Gen): All commits (sha, message)
    - Task 2 (Code Repair): Commits containing 'fix', 'bug', 'patch', 'correct'
    """
    print_status("Task 2 & 4: Collecting Commit Data (Code Repair & Commit Gen)...", is_header=True)
    url = f"{BASE_URL}/commits"
    params = {} # No special params needed for commits
    commits = fetch_paginated_data(url, params, max_items)
    if commits is None: return # Stop if token failed

    # Regex to identify bug-fixing commits
    fix_keywords = re.compile(r'\b(fix(es|ed)?|bug|patch|correct(s|ed)?)\b', re.IGNORECASE)
    
    dataset_code_repair = []
    dataset_commit_gen = []
    
    for commit in commits:
        commit_sha = commit['sha']
        commit_message = commit['commit']['message']
        if len(commit['parents']) > 1: continue # Skip merge commits (they usually don't contain diffs)
            
        commit_data = {
            'sha': commit_sha, 'message': commit_message,
            'author': commit.get('commit', {}).get('author', {}).get('name')
        }
        
        # Task 4: Commit Message Generation (All commits are included in this task)
        dataset_commit_gen.append({'task': 'commit_gen', **commit_data})
        
        # Task 2: Code Repair (Only those containing 'fix')
        if fix_keywords.search(commit_message):
            dataset_code_repair.append({'task': 'code_repair', **commit_data})

    # Save the data separately
    save_to_jsonl('task_4_commit_gen.jsonl', dataset_commit_gen)
    save_to_jsonl('task_2_code_repair.jsonl', dataset_code_repair)

# --- Main Workflow ---

if __name__ == "__main__":
    if GITHUB_TOKEN: # If token was found in .env
        print_status(f"Starting Data Collection from {REPO_OWNER}/{REPO_NAME} Repository", is_header=True)
        if MAX_ITEMS_PER_TASK is None:
            print("[WARNING] MAX_ITEMS_PER_TASK = None. ALL DATA will be fetched. This process may take hours.")
        else:
            print(f"Maximum {MAX_ITEMS_PER_TASK} items will be fetched for each task.")
        
        # Task 1: Code Search (Issues)
        task_1_code_search(MAX_ITEMS_PER_TASK)
        
        # Task 3: Bug Classification (Pull Requests)
        task_3_bug_classification(MAX_ITEMS_PER_TASK)
        
        # Task 2 & 4: Code Repair & Commit Generation (Commits)
        task_2_and_4_commits(MAX_ITEMS_PER_TASK)
        
        print_status("Data Collection (Step 1) Completed!", is_header=True)
        print("Files created:")
        print("- task_1_code_search.jsonl")
        print("- task_2_code_repair.jsonl")
        print("- task_3_bug_classification.jsonl")
        print("- task_4_commit_gen.jsonl")
        print("\n[NEXT STEP] You should run the second script to download the 'diff' data.")
    else:
        # If GITHUB_TOKEN is None
        print("[ERROR] Main workflow could not be started.")
        print("[SOLUTION] Please ensure you have added GITHUB_TOKEN to your .env file.")