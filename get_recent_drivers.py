import os
import requests

def fetch_github_issues():
    """Fetches the last 5 closed issues with the 'drive' label."""
    repo = os.getenv('GITHUB_REPOSITORY', 'adhilsalim/adhilsalim') # Fallback for local testing
    token = os.getenv('GITHUB_TOKEN')
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {'Authorization': f'token {token}'}
    params = {'state': 'all', 'labels': 'drive', 'per_page': 5, 'direction': 'desc'}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub issues: {e}")
        return None

def print_recent_drivers(issues):
    """Prints a markdown list of recent drivers and their commands."""
    if not issues:
        print("No recent drives found.")
        return
        
    print("\n### Recent Drives\n")
    for issue in issues:
        username = issue.get("user", {}).get("login", "Unknown")
        user_url = issue.get("user", {}).get("html_url", "#")
        command = issue.get("title", "N/A")
        print(f"- **[{username}]({user_url})** drove with command: `{command}`")

if __name__ == "__main__":
    issues_data = fetch_github_issues()
    if issues_data:
        print_recent_drivers(issues_data)
