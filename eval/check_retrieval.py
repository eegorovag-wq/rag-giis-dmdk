"""Проверяет только поиск (без модели): на каком месте нужная страница среди найденных фрагментов.

Нужен, чтобы отделить ошибки поиска от ошибок модели.
Запуск: python eval/check_retrieval.py
"""
import json
import math
import pathlib
import re
import urllib.request

HERE = pathlib.Path(__file__).parent
CHUNKS = HERE.parent / "docs" / "giis-dmdk-chunks.txt"
OLLAMA = "http://localhost:11434/api/embed"


def embed(texts):
    body = json.dumps({"model": "bge-m3", "input": texts}).encode("utf-8")
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())["embeddings"]


def cos(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def main():
    chunks = [c for c in CHUNKS.read_text(encoding="utf-8").split("\n\n\n") if c.strip()]
    pages = [int(re.search(r"стр\. (\d+)", c).group(1)) for c in chunks]
    vecs = []
    for i in range(0, len(chunks), 32):
        vecs += embed(chunks[i:i + 32])
    questions = [q for q in json.loads((HERE / "questions.json").read_text(encoding="utf-8")) if q["page"]]
    for q, qv in zip(questions, embed([q["question"] for q in questions])):
        ranked = sorted(range(len(chunks)), key=lambda i: -cos(qv, vecs[i]))
        top = [pages[i] for i in ranked[:8]]
        rank = next((n + 1 for n, i in enumerate(ranked) if pages[i] in (q["page"], q["page"] + 1)), None)
        print(f"{q['id']:>2}. нужна стр.{q['page']}: место {rank}; первые 8 страниц: {top}")


if __name__ == "__main__":
    main()
