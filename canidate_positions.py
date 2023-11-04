import requests
from bs4 import BeautifulSoup
import urllib3
import warnings
import requests
import os
import re

warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)


CANDIDATES = {
    'Democrats': ['Joe Biden', 'Marianne Williamson', 'Cenk Uygur'],
    'Republicans': ['Donald Trump', 'Nikki Haley', 'Vivek Ramaswamy', 'Asa Hutchinson', 'Larry Elder', 'Alaska Binkley', 'Rick Scott', 'Ron DeSantis', 'Mike Pence', 'Chris Christie', 'Doug Burgum'],
    'Independent': ['Joseph Kennedy III', 'Kanye West']
}

def format_name(name):
    return name.replace(' ', '_')

def get_political_positions(candidate):
    formatted_name = format_name(candidate)
    url = f'https://en.wikipedia.org/wiki/Political_positions_of_{formatted_name}'
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()
    return re.sub(r'\n+', '\n', text).strip()  # Remove extra newlines and whitespace

def save_to_text(candidate, content):
    os.makedirs('training/candidates', exist_ok=True)  # ensure the directory exists
    formatted_name = format_name(candidate)
    with open(f'training/candidates/{formatted_name}.txt', 'w', encoding='utf-8') as file:
        file.write(content)

if __name__ == "__main__":
    for party, candidates in CANDIDATES.items():
        for candidate in candidates:
            content = get_political_positions(candidate)
            save_to_text(candidate, content)