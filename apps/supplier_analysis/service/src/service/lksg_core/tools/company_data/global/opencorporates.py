import requests
from bs4 import BeautifulSoup


def search_opencorporates(company_name: str) -> list[dict[str, str]]:
    base_url = "https://opencorporates.com"
    search_url = f"{base_url}/companies?q={company_name.replace(' ', '+')}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch results: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    print(soup)
    return []


# Example usage
company_name = "Tesla"
results = search_opencorporates(company_name)


# Display results
for idx, result in enumerate(results, 1):
    print(f"{idx}. {result['name']}: {result['url']}")
