import os
import requests

def fetch_recent_issues():
    """Fetches the 5 most recent issues from the repository."""
    repo = os.environ.get('GITHUB_REPOSITORY')
    token = os.environ.get('GITHUB_TOKEN')
    
    if not repo or not token:
        print("Error: GITHUB_REPOSITORY or GITHUB_TOKEN environment variables not set.")
        return None

    # Fetch the 5 most recently created issues, regardless of label
    url = f"https://api.github.com/repos/{repo}/issues?state=all&sort=created&direction=desc&per_page=5"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub issues: {e}")
        return None

def format_issue_list(issues):
    """Formats the list of issues into Markdown."""
    if not issues:
        print("### Recent Drivers\n- No one has driven the car recently. Be the first!")
        return

    lines = ["### Recent Drivers"]
    for issue in issues:
        username = issue["user"]["login"]
        command = issue["title"]
        # Sanitize command to prevent markdown injection
        sanitized_command = command.replace('`', '').replace('*', '').replace('_', '')
        
        lines.append(f"- [@{username}](https://github.com/{username}) drove `{sanitized_command}`")
    
    print("\n".join(lines))

if __name__ == "__main__":
    recent_issues = fetch_recent_issues()
    format_issue_list(recent_issues)

