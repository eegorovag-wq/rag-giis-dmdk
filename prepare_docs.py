"""Готовит руководство ГИИС ДМДК для базы знаний.

Что делает:
- берёт текст только страниц с содержанием (без титула, оглавления и журнала изменений);
- убирает служебную рамку листа («Изм.», «Лист», «Подпись и дата» и т.п.);
- режет текст на фрагменты ~900 символов по абзацам;
- в начало каждого фрагмента пишет страницу и раздел, чтобы и поиск, и модель их видели.

Запуск: python prepare_docs.py docs/giis-dmdk-rukovodstvo-5.1.4.pdf docs/giis-dmdk-chunks.txt
"""
import re
import sys

from pypdf import PdfReader

FIRST_PAGE, LAST_PAGE = 12, 229          # 1–11 титул и оглавление, 230+ журнал изменений
CHUNK = 900
SEPARATOR = "\n\n\n"                      # между фрагментами; сплиттер в n8n режет по нему

STAMP = re.compile(
    r"^\s*(Изм\.|Лист|№ докум\.|Подп\.|Дата|Подпись и дата|Взам\. инв\. №|Инв\. № дубл\.|Инв\. № подл\.|"
    r"Изм\. Лист № докум\. Подп\. Дата|\d{1,3})?\s*$"
)
HEADING = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,2})\s+([А-ЯЁA-Z«].{3,120})$")


def clean_lines(text):
    for line in text.splitlines():
        line = line.strip()
        if STAMP.match(line):
            continue
        yield line


def main(src, dst):
    reader = PdfReader(src)
    section = ""
    chunks = []
    for page_no in range(FIRST_PAGE, min(LAST_PAGE, len(reader.pages)) + 1):
        buf, buf_section = "", section
        for line in clean_lines(reader.pages[page_no - 1].extract_text() or ""):
            if len(buf) + len(line) > CHUNK and buf:
                chunks.append((page_no, buf_section, buf.strip()))
                buf = ""
            m = HEADING.match(line)
            # «2 Ограничена …» в примечаниях — не заголовок: у глав без точки названия короткие
            if m and not line.endswith(".") and ("." in m.group(1) or len(line) < 60):
                section = f"{m.group(1)} {m.group(2)}"
            if not buf:
                buf_section = section       # раздел, с которого начинается фрагмент
            buf += line + "\n"
        if buf.strip():
            chunks.append((page_no, buf_section, buf.strip()))

    with open(dst, "w", encoding="utf-8") as f:
        for page_no, sec, body in chunks:
            f.write(f"[Руководство ГИИС ДМДК, стр. {page_no}. Раздел: {sec}]\n{body}{SEPARATOR}")
    print(f"страниц {LAST_PAGE - FIRST_PAGE + 1}, фрагментов {len(chunks)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
