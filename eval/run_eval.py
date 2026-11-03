"""Прогоняет проверочные вопросы через RAG в n8n и сохраняет ответы.

Автоматически отмечает, есть ли в ответе ожидаемый факт и нужная страница.
Итоговую оценку «верно / неверно» я всё равно ставлю вручную, читая ответы:
ключевые слова — только подсказка.

Запуск (n8n и база знаний должны быть запущены): python eval/run_eval.py
"""
import json
import os
import pathlib
import time
import urllib.request

URL = "http://localhost:5678/webhook/giis-ask"
HERE = pathlib.Path(__file__).parent


def ask(question):
    body = json.dumps({"question": question}).encode("utf-8")
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))["output"]


def main():
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    only = {int(x) for x in os.environ.get("EVAL_IDS", "").split(",") if x}
    if only:                                # быстрый прогон части вопросов
        questions = [q for q in questions if q["id"] in only]
    results = []
    for q in questions:
        start = time.time()
        answer = ask(q["question"])
        sec = round(time.time() - start)
        low = answer.lower()
        fact = any(e.lower() in low for e in q["expect"])
        page = q["page"] is None or str(q["page"]) in answer
        results.append({**q, "answer": answer, "seconds": sec, "fact_found": fact, "page_cited": page})
        print(f"{q['id']:>2}. факт={'да' if fact else 'нет'} стр={'да' if page else 'нет'} {sec}с — {answer[:90]!r}")
    out = "results.json" if not only else "results-partial.json"
    (HERE / out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
