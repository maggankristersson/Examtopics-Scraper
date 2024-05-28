import requests
from bs4 import BeautifulSoup
import re
from jinja2 import Template
import argparse
import sys
import time

BASE_URL_TEMPLATE = "https://www.examtopics.com/discussions/cisco/{page}/"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

def get_question_links(test_name, count):
    links = []
    page = 1
    question_prefix = f"Exam {test_name} topic"
    start_time = time.time()
    found = False
    while len(links) < count:
        url = BASE_URL_TEMPLATE.format(page=page)
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error: Unable to fetch page {page}. Status code: {response.status_code}")
            break
        
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a', href=True, string=re.compile(question_prefix)):
            full_url = "https://www.examtopics.com" + link['href']
            match = re.search(r'question (\d+) discussion', link.text)
            if match:
                question_number = match.group(1)
                links.append((question_number, full_url))
                found = True
                if len(links) >= count:
                    break
        
        if not found and (time.time() - start_time) > 50:  # Timeout after 10 seconds if no questions found
            print(f"Error: No questions found '{test_name}'.")
            create_html(links, test_name)
            sys.exit(1)

        page += 1
        print("Current page: " + str(page)) #Print the current page scraped
    return links

def create_html(links, test_name):
    template = Template('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ test_name }} Questions</title>
    </head>
    <body>
        <h1>{{ test_name }} Questions</h1>
        <ul>
        {% for number, link in links %}
            <li><a href="{{ link }}">Question {{ number }}</a></li>
        {% endfor %}
        </ul>
    </body>
    </html>
    ''')
    html_content = template.render(links=links, test_name=test_name)
    with open('questions.html', 'w') as f:
        f.write(html_content)

def main(count, test_name):
    links = get_question_links(test_name, count)
    create_html(links, test_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape questions and create an HTML file.')
    parser.add_argument('-c', '--count', type=int, default=10, help='Number of questions to scrape')
    parser.add_argument('-t', '--test', type=str, required=True, help='Test name to scrape questions for')
    
    args = parser.parse_args()

    try:
        main(args.count, args.test)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
