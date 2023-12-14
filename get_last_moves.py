import requests

def fetch_github_data():
    url = "https://api.github.com/repos/adhilsalim/adhilsalim/issues?state=all&per_page=5"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub data: {e}")
        return None

def print_issue_details(issues):
    if issues is not None:
        for issue in issues:
            username = issue["user"]["login"]
            title = issue["title"]
            print(f"- [{username}](https://github.com/{username}) moved 💗 to {title}")

def main():
    github_data = fetch_github_data()

    if github_data:
        print_issue_details(github_data)

if __name__ == "__main__":
    main()