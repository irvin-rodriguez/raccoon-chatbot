"""
clean_docs.py
Will clean raw HTML files and put them as RAG-ready text.
"""

import os
from bs4 import BeautifulSoup

INPUT_DIR = "./data/html_pages"
OUTPUT_DIR = "./data/clean_text_pages"


def extract_clean_text(html: str) -> str:
    """
    Extract readable text from HTML content.

    Parameters:
        html (str): Raw HTML content of a page.

    Returns:
        str: Cleaned plain text ready for embedding.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove unnecessary tags: scripts, styles, navbars, headers, footers
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Extract only the main content area or use the whole soup
    main = soup.find("div", class_="moose-content") or soup

    # We want to preserve codeblocks so find <pre><code>
    for pre in main.find_all("pre"):
        code = pre.get_text(strip=False)  # preserve the indentation
        # Wrap that code block into markdown keeping the whitespace for indentation
        code_block = f"\n```text\n{code.rstrip()}\n```\n"
        pre.replace_with(code_block)

    # Now extract the text
    text = main.get_text(separator="\n")

    # Strip excessive blank lines
    cleaned_lines = [
        line.strip() for line in text.splitlines() if line.strip()
    ]
    return "\n".join(cleaned_lines)


def clean_all_html(input_dir: str, output_dir: str):
    """
    Goes through the input HTML folder, cleans each file, and writes the cleaned file into output folder.

    Parameters:
        input_dir (str): The path to find the HTML files
        output_dir (str): The path to output the cleaned plain text.
    """
    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith(".html"):
                input_path = os.path.join(root, filename)

                with open(input_path, "r", encoding="utf-8") as f:
                    html = f.read()

                clean_text = extract_clean_text(html)

                # Compute output path, preserving folder structure
                relative_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, relative_path)
                output_path = output_path.replace(".html", ".txt")

                # Make sure the output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(clean_text)

                print(f"[CLEANED] {output_path}")


if __name__ == "__main__":
    print("[INFO] Cleaning HTML files for RAG preparation...")
    clean_all_html(INPUT_DIR, OUTPUT_DIR)
    print("[DONE] All HTML files cleaned and saved.")
