#!/usr/bin/env python3
"""Split the rendered CV into resume, projects, and historic-work PDFs."""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter


PROJECTS_HEADING = "Recent Projects"
HISTORIC_WORK_HEADING = "Historic Work Experience"
EXPECTED_RESUME_PAGES = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create section PDFs from a CV.pdf rendered from CV.tex."
    )
    parser.add_argument("source", nargs="?", type=Path, default=Path("CV.pdf"))
    parser.add_argument(
        "resume", nargs="?", type=Path, default=Path("Resume.pdf")
    )
    parser.add_argument(
        "projects", nargs="?", type=Path, default=Path("Projects.pdf")
    )
    parser.add_argument(
        "historic_work", nargs="?", type=Path, default=Path("HistoricWork.pdf")
    )
    return parser.parse_args()


def find_heading_page(page_texts: list[str], heading: str) -> int:
    matching_pages = [
        page_number
        for page_number, page_text in enumerate(page_texts)
        if heading in page_text
    ]
    if len(matching_pages) != 1:
        raise ValueError(
            f"Expected {heading!r} on exactly one page; found it on "
            f"{len(matching_pages)} pages."
        )
    return matching_pages[0]


def write_pages(
    reader: PdfReader, page_numbers: range, output_path: Path
) -> None:
    writer = PdfWriter()
    for page_number in page_numbers:
        writer.add_page(reader.pages[page_number])

    if reader.metadata:
        metadata = {
            str(key): str(value)
            for key, value in reader.metadata.items()
            if value is not None
        }
        writer.add_metadata(metadata)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as output_file:
        writer.write(output_file)


def main() -> None:
    args = parse_args()
    reader = PdfReader(args.source)
    page_texts = [page.extract_text() or "" for page in reader.pages]

    projects_start = find_heading_page(page_texts, PROJECTS_HEADING)
    historic_work_start = find_heading_page(page_texts, HISTORIC_WORK_HEADING)

    if projects_start != EXPECTED_RESUME_PAGES:
        raise ValueError(
            "The resume must be the first two pages, but the projects section "
            f"starts on page {projects_start + 1}."
        )
    if historic_work_start <= projects_start:
        raise ValueError("The historic-work section must follow the projects section.")

    segments = (
        (args.resume, range(0, projects_start)),
        (args.projects, range(projects_start, historic_work_start)),
        (args.historic_work, range(historic_work_start, len(reader.pages))),
    )

    if any(len(page_numbers) == 0 for _, page_numbers in segments):
        raise ValueError("Each generated PDF must contain at least one page.")

    for output_path, page_numbers in segments:
        write_pages(reader, page_numbers, output_path)

    generated_page_count = 0
    summaries = []
    for output_path, expected_pages in segments:
        output_reader = PdfReader(output_path)
        actual_page_count = len(output_reader.pages)
        if actual_page_count != len(expected_pages):
            raise ValueError(
                f"{output_path} has {actual_page_count} pages; expected "
                f"{len(expected_pages)}."
            )
        generated_page_count += actual_page_count
        summaries.append(f"{output_path}: {actual_page_count} pages")

    if generated_page_count != len(reader.pages):
        raise ValueError("The section PDFs do not account for every page in the CV.")

    print(f"{args.source}: {len(reader.pages)} pages")
    for summary in summaries:
        print(summary)


if __name__ == "__main__":
    main()
