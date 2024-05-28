import requests
from bs4 import BeautifulSoup
import re
from jinja2 import Template
import argparse
import sys
import time
import threading
import keyboard
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

BASE_URL_TEMPLATE = "https://www.examtopics.com/discussions/cisco/{page}/"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

MAX_PAGE = 660
stop_scraping = False

def get_question_links(test_name, count, keywords=None, debug=False):
    global stop_scraping
    links = []
    page = 1
    question_prefix = f"Exam {test_name} topic"
    start_time = time.time()

    while page <= MAX_PAGE and (count == sys.maxsize or len(links) < count):
        if stop_scraping:
            print(Fore.RED + "Stopping scraping...")
            break

        url = BASE_URL_TEMPLATE.format(page=page)
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(Fore.RED + f"Error: Unable to fetch page {page}. Status code: {response.status_code}")
            break
        
        soup = BeautifulSoup(response.content, 'html.parser')

        for link in soup.find_all('a', href=True, string=re.compile(question_prefix)):
            full_url = "https://www.examtopics.com" + link['href']
            match = re.search(r'question (\d+) discussion', link.text)
            if match:
                question_number = match.group(1)
                if keywords:
                    question_page = requests.get(full_url, headers=HEADERS)
                    question_soup = BeautifulSoup(question_page.content, 'html.parser')
                    question_text = question_soup.get_text()
                    found_keyword = False
                    for keyword in keywords:
                        if keyword.lower() in question_text.lower():
                            links.append((question_number, full_url, keyword))
                            found_keyword = True
                            print(Fore.GREEN + f"Found question {question_number} with keyword '{keyword}'")
                            break
                    if not found_keyword:
                        continue
                else:
                    links.append((question_number, full_url, "None"))
                    print(Fore.GREEN + f"Found question {question_number}")
                if count != sys.maxsize and len(links) >= count:
                    break
        else:
            page += 1
            print(Fore.CYAN + f"Page[{page}]")
            continue
        break

    if count == sys.maxsize:
        print(Fore.YELLOW + "Scraping all pages...")
    elif len(links) < count:
        print(Fore.YELLOW + f"Warning: The specified count of {count} may not be reached. Consider using 'max' for unlimited scraping.")

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
        {% for number, link, keyword in links %}
            <li>
                <a href="{{ link }}">Question #{{ number }}</a> (Keyword: {{ keyword }})
            </li>
        {% endfor %}
        </ul>
    </body>
    </html>
    ''')
    html_content = template.render(links=links, test_name=test_name)
    with open('questions.html', 'w') as f:
        f.write(html_content)
    print(Fore.GREEN + "Done!")

def main(count, test_name, keywords=None, debug=False):
    global stop_scraping
    if count.lower() == 'max':
        count = sys.maxsize
    else:
        count = int(count)
    if keywords:
        keywords = keywords.split(',')
        if len(keywords) >= 1:
            print(Fore.YELLOW + "Warning: Specifying keywords may increase execution time significantly.")

    def listen_for_quit():
        global stop_scraping
        keyboard.wait('q')
        stop_scraping = True

    quit_listener = threading.Thread(target=listen_for_quit, daemon=True)
    quit_listener.start()

    links = get_question_links(test_name, count, keywords, debug)
    create_html(links, test_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Scrape questions and create an HTML file.',
        epilog='''
        Examples:
          scraper.py -c 10 -t 350-401 -k BGP,OSPF,RIP
          scraper.py -c max -t 350-401 -k BGP

        Notes:
          - Press 'q' at any time to stop the scraping process and generate the HTML file with the results gathered so far.
          - Using multiple keywords may significantly increase the execution time.
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-c', '--count', type=str, default='max', help='Number of questions to scrape (or "max" for all (which is default))')
    parser.add_argument('-t', '--test', type=str, required=True, help='Test name to scrape questions for')
    parser.add_argument('-k', '--keywords', type=str, help='Keywords to filter questions (comma-separated)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    try:
        main(args.count, args.test, args.keywords, args.debug)
    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}")
        sys.exit(1)
