"""
scrape_docs.py
Will scrape RACOON website for its documentation and save raw HTML files.
"""

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from tqdm import tqdm

BASE_URL = "https://hugary1995.github.io/raccoon/index.html"
OUTPUT_DIR = "./data/html_pages"


def is_internal_link(href: str) -> bool:
    """
    Checks whether a given href link is:
    - not None or empty
    - ends with '.html'
    - stays within the RACCOON documentation site
    """
    return (href and href.endswith(".html")
            and "hugary1995.github.io/raccoon" in href)


def get_all_links(base_url: str) -> list[str]:
    """
    Crawls the base URL and collects all internal documentation links.

    Parameters:
        base_url (str): Starting page to crawl from.

    Returns:
        list of str: All internal links discovered as absolute URLs.
    """

    visited = set()  # avoid going to a URL multiple times
    to_visit = [base_url]  # queue for BFS-style crawling
    all_links = set()  # unique HTML page links

    print("[INFO] Starting crawl from: ", base_url)

    with tqdm(total=1, desc="Crawling pages") as pbar:
        while to_visit:
            current_url = to_visit.pop()
            if current_url in visited:
                continue

            # make HTTP GET request to get page content
            # raise an error if status code is not 200 (aka successful response)
            # parse HTML content into a BeautifulSoup object
            # mark the current URL as visited
            # save links found
            try:
                response = requests.get(current_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                visited.add(current_url)
                all_links.add(current_url)

            # announce error and continue on
            except requests.RequestException as e:
                print(f"[ERROR] Failed to fetch {current_url}: {e}")
                continue

            # find the valid links found in our current URL
            # get the link desitantion and convert to a full URL
            for link in soup.find_all("a", href=True):
                href = link["href"]
                joined_url = urljoin(current_url, href)

                # if the link stays within the site and we have not visited it before
                # mark it as one we should visit
                if is_internal_link(joined_url) and joined_url not in visited:
                    to_visit.append(joined_url)
                    pbar.total += 1

            pbar.update(1)

    print("[INFO] Finished crawl from: ", base_url)

    return sorted(all_links)


def save_html_page(url: str, output_dir: str):
    """
    Downloads the HTML content of a given URL and saves it to disk.

    Parameters:
        url (str): The full URL of the HTML page going to be downloaded.
        output_dir (str): Directory where the HTML files will be saved.

    Saves:
        A `.html` file names after the last part of the URL
    """

    try:
        # get HTML GET response to get page content and check 200 response
        # parse url and assign filename based on basename of URL
        response = requests.get(url)
        response.raise_for_status()

        parsed_url = urlparse(url)
        relative_path = parsed_url.path.lstrip("/")
        
        if relative_path.startswith("raccoon/"):
            relative_path = relative_path[len("raccoon/"):]

        filepath = os.path.join(output_dir, relative_path)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # write HTML content into the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"[SAVED] {filepath}")

    except requests.RequestException as e:
        print(f"[ERROR] Could not save {url}: {e}")

    except OSError as e:
        print(f"[ERROR] Could not save file {filepath}: {e}")


if __name__ == "__main__":
    print("[INFO] Starting RACOON doc scraping...")

    links = get_all_links(BASE_URL)
    print(f"[INFO] Found {len(links)} pages.")

    for link in tqdm(links, desc="Downloading pages"):
        save_html_page(link, OUTPUT_DIR)

    print("[DONE] All pages downloaded.")
