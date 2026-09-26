#!/usr/bin/env python3
"""Convert the SPL question bank into lookups/spl_quiz_questions.csv.

Accepts either a JSON array file (e.g. splunk_mcq_questions.json) or NDJSON (one
question object per line).  Two option layouts are understood:

  * list:  "options": ["A) text", "B) text", "C) text", "D) text"]
  * dict:  "options": {"A": "text", "B": "text", "C": "text", "D": "text"}

Output columns:
  qid, category, question, option_a, option_b, option_c, option_d, correct_answer, explanation

Leading "A) " / "B) " / "C) " / "D) " prefixes are stripped and correct_answer is
forced to upper case.  The category is taken from the "category" key when present,
otherwise from --category-field (default "chapter"; use "subtopic" for a finer split).

Usage:
  python3 bin/build_lookup.py SOURCE.json [--out lookups/spl_quiz_questions.csv]
                              [--category-field chapter]
"""
import argparse, csv, json, os, re, sys

COLS = ["qid", "category", "question", "option_a", "option_b", "option_c",
        "option_d", "correct_answer", "explanation"]
PREFIX = re.compile(r"^\s*[A-Da-d]\)\s*")


def load(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read().strip()
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(l) for l in text.splitlines() if l.strip()]


def clean(s):
    return re.sub(r"\s+", " ", str(s if s is not None else "")).strip()


def options(q):
    o = q["options"]
    if isinstance(o, dict):
        vals = [o[k] for k in ("A", "B", "C", "D")]
    else:
        vals = list(o)
    if len(vals) != 4:
        raise ValueError("question %s does not have 4 options" % q.get("id"))
    return [clean(PREFIX.sub("", str(v), count=1)) for v in vals]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--out", default=os.path.join(here, "..", "lookups", "spl_quiz_questions.csv"))
    ap.add_argument("--category-field", default="chapter")
    a = ap.parse_args()

    rows, seen = [], set()
    for q in load(a.source):
        qid = q["id"]
        if qid in seen:
            sys.exit("duplicate id %s" % qid)
        seen.add(qid)
        ans = clean(q["correct_answer"]).upper()
        if ans not in ("A", "B", "C", "D"):
            sys.exit("bad correct_answer for id %s: %r" % (qid, ans))
        cat = clean(q.get("category") or q.get(a.category_field) or "General")
        oa, ob, oc, od = options(q)
        rows.append([qid, cat, clean(q["question"]), oa, ob, oc, od, ans, clean(q.get("explanation"))])

    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
        w.writerow(COLS)
        w.writerows(rows)
    print("wrote %d rows to %s" % (len(rows), os.path.abspath(a.out)))


if __name__ == "__main__":
    main()
