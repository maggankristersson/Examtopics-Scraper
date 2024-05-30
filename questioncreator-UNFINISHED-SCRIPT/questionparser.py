import os
import requests
from bs4 import BeautifulSoup
import json
import random
import time
from fake_useragent import UserAgent

# Ensure output-images directory exists
if not os.path.exists('output-images'):
    os.makedirs('output-images')

# Function to fetch the HTML content with retries and random user agents
def fetch_html(url, retries=5, delay=5):
    ua = UserAgent()
    for attempt in range(retries):
        try:
            headers = {'User-Agent': ua.random}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.content
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay + random.uniform(0, delay))  # Wait before retrying
            else:
                print("All attempts failed.")
                return None

# Function to download an image and save it to the output-images folder
def download_image(image_url, question_number, alt_label=None, index=None):
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        # Extract the file extension from the image URL
        file_extension = os.path.splitext(image_url)[1]
        if index is not None:
            file_name = f"output-images/{question_number}_{index}{file_extension}"
        elif alt_label:
            file_name = f"output-images/{question_number}_{alt_label}{file_extension}"
        else:
            file_name = f"output-images/{question_number}{file_extension}"
        with open(file_name, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Downloaded image: {file_name}")
        return file_name
    except requests.RequestException as e:
        print(f"Failed to download image {image_url}: {e}")
        return None

# Function to parse the HTML content and extract the required fields
def parse_html(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the question number from the URL
    question_number = url.split('question')[1].split('discussion')[0].strip('-').strip('/')

    # Extract the question text
    question_text = soup.find('div', class_='question-body').find('p', class_='card-text').get_text(separator=' ', strip=True)

    # Extract the images within the question text
    images = [img['src'] for img in soup.find('div', class_='question-body').find_all('img')]

    # Download images and save them with the question number as the file name
    local_images = []
    alt_images = {}
    alt_label_counter = 0
    index = 1
    for image_url in images:
        alt_label = None
        # Check if the image is used as an alternative answer
        alt_label_letter = image_url.split('/')[-1].split('.')[0]
        if alt_label_letter in ['A', 'B', 'C', 'D']:
            alt_label = alt_label_letter
            alt_label_counter += 1
        local_image_path = download_image(image_url, question_number, alt_label, index)
        if local_image_path:
            if alt_label:
                alt_images[alt_label] = local_image_path
            else:
                local_images.append(local_image_path)
        index += 1

    # Extract answer choices if available
    choices_container = soup.find('div', class_='question-choices-container')
    answers = []
    if choices_container:
        answers = [choice.get_text(separator=' ', strip=True) for choice in choices_container.find_all('li', class_='multi-choice-item')]

    # Extract the correct/voted answer from the JSON script if available
    script_tag = soup.find('script', type='application/json')
    suggested_answer = None
    voted_answer = None
    if script_tag:
        json_content = json.loads(script_tag.string)
        suggested_answer = json_content[0]['voted_answers']
        voted_answer = json_content[0]['voted_answers']

    # If suggested_answer is null, assign the last image as the suggested answer
    if suggested_answer is None and local_images:
        suggested_answer = local_images[-1]

    return {
        "question_number": question_number,
        "question_text": question_text,
        "answers": answers,
        "images": local_images,
        "alt_images": alt_images,
        "suggested_answer": suggested_answer,
        "voted_answer": voted_answer
    }

# Main script execution
def main():
    # Read URLs from the file
    with open('urls.txt', 'r') as file:
        urls = file.readlines()

    with open('output.json', 'w') as json_file:
        json_file.write("[\n")
        for idx, url in enumerate(urls):
            url = url.strip()
            print(f"Processing URL: {url}")
            html_content = fetch_html(url)
            if html_content:
                data = parse_html(html_content, url)
                print(f"Question Number: {data['question_number']}")
                print(f"Question: {data['question_text']}")
                print("Answers:")
                for answer in data['answers']:
                    print(answer)
                print("Images:")
                for image in data['images']:
                    print(image)
                for alt_label, alt_image in data['alt_images'].items():
                    print(f"Alternative Image {alt_label}: {alt_image}")
                print(f"Suggested Answer: {data['suggested_answer']}")
                print(f"Voted Answer: {data['voted_answer']}")
                # Write each data entry as a separate JSON object followed by a comma and a newline character
                json.dump(data, json_file, indent=4)
                if idx < len(urls) - 1:
                    json_file.write(",\n")
                else:
                    json_file.write("\n")
        json_file.write("]\n")


# Run the script
if __name__ == "__main__":
    main()
