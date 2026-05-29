from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import bs4
import requests
from pypdf import PdfWriter

INTRO = ["dedication.pdf", "preface.pdf", "toc.pdf"]
APPENDICES = [
    "dialogue-vmm.pdf",
    "vmm-intro.pdf",
    "dialogue-monitors.pdf",
    "threads-monitors.pdf",
    "dialogue-labs.pdf",
    "lab-tutorial.pdf",
    "lab-projects-systems.pdf",
    "lab-projects-xv6.pdf",
]


def scrape_urls2() -> None:
    url = "http://pages.cs.wisc.edu/~remzi/OSTEP/#book-chapters"
    resp = requests.get(url)
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    base_url = "http://pages.cs.wisc.edu/~remzi/OSTEP/{}"
    rslt: dict[int, str] = {}

    # insert intro
    for i, cha_url in enumerate(INTRO):
        i += 100
        rslt[i] = base_url.format(cha_url)

    for link in soup.find_all("td"):
        el = link.find("small")
        small_text = el.get_text() if el else ""
        a_tag = link.find("a")
        href = a_tag.attrs["href"] if a_tag and "href" in a_tag.attrs else ""
        try:
            chapter = int(small_text) + 200
        except (ValueError, TypeError):
            chapter = None
        if chapter and href:
            rslt[chapter] = base_url.format(href)

    # insert appendices
    for i, cha_url in enumerate(APPENDICES):
        i += 900  # append to the end
        rslt[i] = base_url.format(cha_url)

    with open("./urls.txt", "w", encoding="utf-8") as f:
        for k in sorted(rslt.keys()):
            print(k, rslt[k], file=f)


def download_book() -> None:
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)

    def download(index: str, url: str) -> None:
        url = url.strip()
        print(f"  {index} downloading {url}")
        res = requests.get(url, timeout=120)
        print(res)
        if res.ok:
            filename = url.split("/")[-1]
            dest = output_dir / f"{index}-{filename}"
            print(f"{filename} -> {dest}")
            dest.write_bytes(res.content)

    with open("./urls.txt", encoding="utf-8") as f:
        tasks = [line.split(" ", 1) for line in f if line.strip()]

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(download, i.strip(), url.strip()) for i, url in tasks
        }
        for future in as_completed(futures):
            future.result()  # re-raise any download exceptions


def merge_pdf() -> None:
    output_dir = Path("./output")
    files = sorted(output_dir.glob("*.pdf"))

    writer = PdfWriter()
    for pdf in files:
        writer.append(pdf)
    with open("OSTEP.pdf", "wb") as fout:
        writer.write(fout)
    writer.close()


def read_file() -> None:
    with open("./urls.txt", encoding="utf-8") as f:
        for line in f:
            index, url = line.split(" ", 1)
            print(f"{index}{url}")


if __name__ == "__main__":
    scrape_urls2()
    download_book()
    merge_pdf()
    # read_file()
