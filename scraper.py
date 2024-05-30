import httpx
import asyncio
from bs4 import BeautifulSoup
import re
from jinja2 import Template
import argparse
import sys
import time
import threading
import keyboard
from colorama import init, Fore
from fake_useragent import UserAgent
import random

# Initialize colorama
init(autoreset=True)

BASE_URL_TEMPLATE = "https://www.examtopics.com/discussions/cisco/{page}/"
MAX_PAGE = 660
stop_scraping = False

ua = UserAgent()

def get_headers():
    return {'User-Agent': ua.random}

async def fetch(client, url, headers):
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as e:
        print(Fore.RED + f"Error: Unable to fetch page. Status code: {e.response.status_code}")
        return None

async def get_question_links(test_name, count, keywords=None, debug=False):
    global stop_scraping
    links = []
    page = 1
    question_prefix = f"Exam {test_name} topic"
    async with httpx.AsyncClient() as client:
        while page <= MAX_PAGE and (count == sys.maxsize or len(links) < count):
            if stop_scraping:
                print(Fore.RED + "Stopping scraping...")
                break

            url = BASE_URL_TEMPLATE.format(page=page)
            headers = get_headers()

            debug_time_page_main_start = time.time()

            response = await fetch(client, url, headers)
            if response is None:
                break

            print(Fore.CYAN + f"Page[{page}]...")

            debug_time_page_main = time.time() - debug_time_page_main_start
            if debug:
                print("DEBUG: Main page response time " + str(round(debug_time_page_main, 2)) + "ms")

            soup = BeautifulSoup(response.content, 'html.parser')

            for link in soup.find_all('a', href=True, string=re.compile(question_prefix)):
                debug_start_time = time.time()

                full_url = "https://www.examtopics.com" + link['href']
                match = re.search(r'question (\d+) discussion', link.text)
                if match:
                    question_number = match.group(1)
                    if keywords:
                        debug_time_keyword_start = time.time()
                        question_page = await fetch(client, full_url, headers)
                        if question_page is None:
                            continue
                        question_soup = BeautifulSoup(question_page.content, 'html.parser')
                        question_text = question_soup.get_text()
                        found_keyword = False
                        for keyword in keywords:
                            if debug:
                                print(f"DEBUG: [Looking for keyword '{keyword}'] in {question_number}")
                            if keyword.lower() in question_text.lower():
                                links.append((question_number, full_url, keyword))
                                found_keyword = True
                                print(Fore.GREEN + f"Found question {question_number} with keyword '{keyword}'")
                                break
                        debug_time_keyword = time.time() - debug_time_keyword_start
                        if debug:
                            print("DEBUG: Keyword response time " + str(round(debug_time_keyword, 2)) + "ms")
                        if not found_keyword:
                            links.append((question_number, full_url, "None"))
                            print(Fore.GREEN + f"Found question {question_number}")                       
                    if count != sys.maxsize and len(links) >= count:
                        break

            page += 1
            await asyncio.sleep(random.uniform(1, 3))  # Random delay between requests

    if count == sys.maxsize:
        print(Fore.YELLOW + "Scraping all pages...")
    elif len(links) < count:
        print(Fore.YELLOW + f"Warning: The specified count of {count} may not be reached. Consider using 'max' for unlimited scraping.")

    return links

def create_html(links, test_name):
    number_of_questions = len(links)
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
        <h2>{{ number_of_questions }} questions:</h2>
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
    html_content = template.render(links=links, test_name=test_name, number_of_questions=number_of_questions)
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
        print(Fore.RED + "Stops scraping due to Q being pressed")
        stop_scraping = True

    quit_listener = threading.Thread(target=listen_for_quit, daemon=True)
    quit_listener.start()

    links = asyncio.run(get_question_links(test_name, count, keywords, debug))
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