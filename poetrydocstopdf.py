import os
import re

from bs4 import BeautifulSoup
import fitz
from markdown2 import markdown_path
import requests
from weasyprint import HTML


class PoetryDocumentationGenerator:
    def __init__(self):
        self.urls_to_retrieve = []

    def remove_metadata(self, md_file_name):
        with open(md_file_name, "r") as fp:
            md_data = fp.read()
        search = re.search('title: "(.*?)"', md_data)
        if md_data[0:3] == "---":
            md_data = md_data[md_data.find("---", 5) + 3 :].strip()
            if search[1] == "Introduction":
                md_data = md_data.replace(
                    "# Introduction", "# Poetry for Python — Introduction"
                )
            with open(md_file_name, "w", encoding='utf-8') as fp:
                fp.write(md_data)
        return search[1]

    def convert_markdown_to_pdf(self, filename, output=None):
        html = markdown_path(filename)
        HTML(string=html).write_pdf(output, stylesheets=["mou.css"])

    def get_poetry_documentation_order(self):
        r = requests.get("https://python-poetry.org/docs/")
        soup = BeautifulSoup(r.text, features="html.parser")
        hrefs = soup.find_all("a")
        for href in hrefs:
            if (
                "class" in href.attrs
                and "-m-3" in href.attrs["class"]
                and "/master/" not in href.attrs["href"]
            ):
                href = href.attrs["href"]
                if href == "/docs/":
                    href = "/docs/_index/"
                href = (
                    "https://raw.githubusercontent.com/python-poetry/poetry/master"
                    + href[:-1]
                    + ".md"
                )
                if href not in self.urls_to_retrieve:
                    self.urls_to_retrieve.append(href)

    def download_doc_file(self, url_to_retrieve):
        r = requests.get(url_to_retrieve)
        doc_filename = "temp.md"
        with open(doc_filename, "w", encoding="utf-8") as fp:
            fp.write(r.text)
        return doc_filename

    def build_pdf(self):
        self.get_poetry_documentation_order()
        output_pdf = fitz.open()
        pdf_toc = []
        page_num = 1
        for idx, url_to_retrieve in enumerate(self.urls_to_retrieve):
            doc_filename = self.download_doc_file(url_to_retrieve)
            bookmark_title = self.remove_metadata(doc_filename)
            pdf_toc.append([1, bookmark_title, page_num])
            temp_pdf_filename = "temp.pdf"
            self.convert_markdown_to_pdf(doc_filename, output=temp_pdf_filename)
            with fitz.open(temp_pdf_filename) as mfile:
                output_pdf.insert_pdf(mfile)
                page_num += mfile.pageCount
                mfile.close()  # yes, we are in a context manager but avoid handle problems
            os.remove(doc_filename)
            os.remove(temp_pdf_filename)
        output_pdf.set_toc(pdf_toc)
        output_pdf_filename = "PythonPoetryDocumentation.pdf"
        output_pdf.save(output_pdf_filename)
        print("PDF generation complete")
        os.startfile(output_pdf_filename)


def main():
    pdg = PoetryDocumentationGenerator()
    pdg.build_pdf()


if __name__ == "__main__":
    main()
