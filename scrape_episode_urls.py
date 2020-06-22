"""
This module extracts the transcripts for all Avatar: The Legend of Aang episodes.
"""
import requests
from bs4 import BeautifulSoup

import sys
import os
import re
import csv
from collections import defaultdict

BASE_URL = "https://transcripts.fandom.com"
WIKI_URL = "https://transcripts.fandom.com/wiki/Avatar:_The_Last_Airbender"
OUTPUT_DIR = "raw_data"
OUTPUT_FILENAME = "transcript_{}_{}_{}.csv"
BOOK_IDS = ["Book_One:_Water", "Book_Two:_Earth", "Book_Three:_Fire"]


def create_output_folder(folder_name=OUTPUT_DIR):
    """Create the output folder for the transcripts, if it does not already exist.

    Args:
        folder_name (str): the name of the output folder
    """
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)


def fetch_html_content(url=WIKI_URL):
    """Fetch the HTML content of the given URL. Returns None if the status code is not 200.

    Args:
        url (str): URL of an HTML webpage

    Returns:
        The byte content of the given webpage.
    """
    r = requests.get(url)
    if r.status_code != 200:
        sys.stderr.write("ERROR. Couldn't fetch the main page.\n")
        sys.exit(2)
    return r.content


def extract_transcript_urls(page_content):
    """Parse the HTML content and find all links to the pages containing the actual transcriptions.
    The URLs are relative to the base URL (transcripts.fandom.com).
    Episodes that were split into parts point to the same URL.

    Args:
        page_content (byte): HTML content of the main page

    Returns:
        A dictionary mapping the relative URL to a list of (book number, episode number, episode title) tuples
    """
    urls_dict = defaultdict(list)
    soup = BeautifulSoup(page_content, features="html.parser")

    for book_number, book_id in enumerate(BOOK_IDS, 1):
        book_content = soup.find(id=book_id).parent.next_sibling.next_sibling.find_all("tr")[0]
        for table_row in book_content.find_all("tr"):
            episode_number = int(table_row.find("th").text.strip('\n '))
            link = table_row.find("a")
            urls_dict[link.get("href")].append((book_number, episode_number, link.text))

    return urls_dict


def extract_transcripts_to_files(output_dir, urls_dict):
    """For each URL, fetch the page content and extract the transcripts of each episode into separate files.

    Most pages contain the transcript for a single episode, but episodes that were aired as several parts
    are regrouped in the same page. In that case, each part will be written to an individual file.

    The output is written to a CSV in the output_dir using the following format for the filename:
        transcript_{book number}_{episode number}_{title}.csv
    This will override any existing files with the same name.

    Args:
        output_dir (str): name of the output directory
        urls_dict (dict): A dictionary mapping the relative URL to
            a list of (book number, episode number, episode title) tuples
    """
    for url, episodes in urls_dict.items():
        content = fetch_html_content(BASE_URL + url)
        if not content:
            sys.stderr.write("ERROR. Couldn't fetch the transcript from {}.\n".format(url))
            sys.exit(2)
        soup = BeautifulSoup(content, features="html.parser")
        main_body = soup.find(id="WikiaArticle")

        if len(episodes) == 1:
            create_transcript_for_episode(output_dir, main_body, episodes[0])
        else:
            for part_number, episode in enumerate(episodes, 1):
                part_title = main_body.find("span", text=re.compile('^Part {}'.format(part_number))).parent
                part_body = part_title.next_sibling.next_sibling
                create_transcript_for_episode(output_dir, part_body, episode)


def create_transcript_for_episode(output_dir, episode_content, episode_info):
    """Extract and write the transcriptions for one episode to a file.

    The output is written to a CSV in the output_dir using the following format for the filename:
        transcript_{book number}_{episode number}_{title}.csv

    Args:
        output_dir (str): name of the output directory
        episode_content (bs4.element.Tag): the HTML elements containing the dialog for the given episode
        episode_info (tuple): containing (book_number, episode_number, episode_name)
    """
    book_number, episode_number, episode_name = episode_info
    output = []

    for character in episode_content.find_all("th"):
        if character.next_sibling:
            line = character.next_sibling.text.strip("\n")
            while '[' in line:
                line = re.sub(r"\[[^\]]*\] ?", "", line)
            if line.strip():
                output.append((character.text.strip("\n"), line))

        filename = os.path.join(
            output_dir,
            OUTPUT_FILENAME.format(
                book_number,
                episode_number,
                episode_name.replace(',', '').replace(' ', '_')
            )
        )
        with open(filename, "w", newline="\n", encoding="utf-8") as file:
            for row in output:
                writer = csv.writer(file)
                writer.writerow([row[0], row[1]])


if __name__ == "__main__":

    create_output_folder()
    html_content = fetch_html_content()

    print("Copying all transcripts to raw_data/ ...")

    transcript_urls = extract_transcript_urls(html_content)
    extract_transcripts_to_files(OUTPUT_DIR, transcript_urls)

    print("Done.")
