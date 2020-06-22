"""
This module extracts the transcripts for all episodes into the raw_data/ folder.
"""

import sys
import os
import requests
import re
import csv
from bs4 import BeautifulSoup

BASE_URL = "https://transcripts.fandom.com"
WIKI_URL = "https://transcripts.fandom.com/wiki/Avatar:_The_Last_Airbender"
UNWANTED_URL = "https://avatar.fandom.com/wiki/Avatar_Wiki:Transcripts"
UNAIRED_PILOT_URL = "/wiki/Unaired_pilot_(Avatar:_The_Last_Airbender)"
OUTPUT_DIR = "raw_data"
OUTPUT_FILENAME = "transcript_{}.csv"


def create_output_folder(folder_name=OUTPUT_DIR):
    """Creates the given output directory if it doesn't exist."""
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)


def fetch_html_content(url=WIKI_URL):
    """Fetches the HTML content of the given URL. Returns None if the status code is not 200."""
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.content


def extract_transcript_urls(page_content):
    """Parse the HTML content and find all links to the transcript pages"""
    urls = []

    soup = BeautifulSoup(page_content, features="html.parser")

    for tr in soup.find(id="mw-content-text").find_all("tr"):
        for link in tr.find_all('a'):
            urls.append(link.get('href'))
    urls.remove(UNWANTED_URL)
    urls.remove(UNAIRED_PILOT_URL)
    return urls


def extract_transcripts_to_files(urls):
    """For each url, fetch the page and extract the text into a file"""
    file_nb = 1
    for url in urls:
        content = fetch_html_content(BASE_URL + url)
        if not content:
            sys.stderr.write("ERROR. Couldn't fetch the transcript from {}.\n".format(url))
            sys.exit(2)
        soup = BeautifulSoup(content, features="html.parser")

        output = []
        for character in soup.find(id="WikiaArticle").find_all("th"):
            if character.next_sibling:
                line = character.next_sibling.text.strip("\n")
                line = re.sub(r"\[.*\] ?", "", line)
                if line.strip():
                    output.append((character.text.strip("\n"), line))

        filename = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME.format(file_nb))
        with open(filename, "w", newline="\n", encoding="utf-8") as file:
            for row in output:
                writer = csv.writer(file)
                writer.writerow([row[0], row[1]])
        file_nb += 1


if __name__ == "__main__":

    create_output_folder()

    html_content = fetch_html_content()

    if not html_content:
        sys.stderr.write("ERROR. Couldn't fetch the main page.\n")
        sys.exit(2)

    print("Copying all transcripts to raw_data/ ...")

    transcript_urls = extract_transcript_urls(html_content)

    extract_transcripts_to_files(transcript_urls)

    print("Done.")
