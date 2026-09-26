# splunk-foo-quiz

A self-contained **SPL knowledge quiz** for Splunk, built entirely with **Dashboard Studio** dashboards and plain **CSV lookups**. It serves random multiple-choice questions about the Search Processing Language, scores each user, and shows a leaderboard.

- **2,500 multiple-choice questions** covering search commands, eval functions, statistical and charting functions, time modifiers, internal commands and the CLI
- **Randomized, per-user delivery**: you never see a question you have already answered
- **Instant feedback** with a correct/incorrect verdict and an explanation
- **Category filter**: quiz yourself on one command type, function family, or everything
- **Per-user scoring and a leaderboard** with category breakdowns and full answer history
- **No KV Store, no custom code, no add-ons**: two dashboards, two CSV lookups, and a few `.conf` files

> **Screenshots:** add `docs/quiz.png` and `docs/leaderboard.png` here before publishing.

---

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Using the quiz](#using-the-quiz)
- [Using the leaderboard](#using-the-leaderboard)
- [The question bank](#the-question-bank)
- [Categories](#categories)
- [Repository layout](#repository-layout)
- [Rebuilding the questions lookup](#rebuilding-the-questions-lookup)
- [Resetting scores](#resetting-scores)
- [Design notes and known limitations](#design-notes-and-known-limitations)
- [Question quality](#question-quality)
- [License and attribution](#license-and-attribution)

---

## How it works

The app ships two Dashboard Studio (`version="2"`) views:

| View | Purpose |
|---|---|
| `spl_foo_quiz` | Shows one random unanswered question at a time, records the answer, shows the verdict and explanation, and tracks your running score |
| `spl_foo_leaderboard` | Ranks all users and lets you drill into one user's category performance, unanswered questions, and answer history |

State lives in two CSV lookups:

| Lookup | Contents |
|---|---|
| `spl_quiz_questions.csv` | The question bank (generated, 2,500 rows) |
| `spl_quiz_results.csv` | The answer log, appended to with `\| outputlookup append=true` |

The current Splunk user is taken from the `$env:user$` token, so there is nothing to sign in to. Every scoring search collapses repeat clicks with `stats latest(is_correct) ... by user qid`, so answering the same question twice never double-counts.

## Requirements

- Splunk Enterprise with **Dashboard Studio** (developed and run on Splunk Enterprise 9.4)
- A role that can write lookup files in the app. `default.meta` grants write access to `admin`, `power` and `user`
- Nothing else: **no KV Store, no add-ons, no scripts at runtime**

## Install

1. Download `splunk-foo-quiz.tar.gz` from this repository.
2. In Splunk Web go to **Apps -> Manage Apps -> Install app from file**.
3. Choose the archive and click **Upload** (tick *Upgrade app* if you are replacing an older copy).
4. Open **Splunk Foo Quiz** from the app menu. The quiz is the default view.

To build the archive yourself from a checkout:

```bash
tar -czf splunk-foo-quiz.tar.gz splunk-foo-quiz/
```

If you cannot install apps, each dashboard's definition is also saved under `splunk-foo-quiz/README/` (`spl_foo_quiz.studio.json`, `spl_foo_leaderboard.studio.json`). Create a blank Dashboard Studio dashboard, open **Edit -> Source**, and paste the JSON in. You will still need the two lookups.

## Using the quiz

1. Pick the categories you want in the **Categories** box (the default is everything).
2. Read the question and click one of the four choices in the **Choose One** table.
3. The **Result** panel shows **CORRECT** or **INCORRECT**, your answer, the right answer, and an explanation.
4. Click **NEXT QUESTION** (or *skip this question*) for another random question. Your category selection is kept.

The header shows how many questions you have answered, how many you got right, and your overall percentage. The right-hand table breaks your score down by category.

## Using the leaderboard

- **Overall Standings**: every user ranked by percent correct, with answered, correct and remaining counts. Click a user name to focus the other panels on that person. With no user selected, the panels show everyone combined.
- **Category % Correct - All Users**: a user-by-category matrix.
- **Category Breakdown** and **Unanswered by Category**: for the selected user (or all users).
- **Answer History**: newest first, one row per question. Click anywhere on a row to load that question.
- **Question Detail**: the full question, all four options, the correct answer and the explanation for the selected row.

## The question bank

`splunk_mcq_questions.json` holds the 2,500 questions. Each entry looks like this:

```json
{
  "id": 1327,
  "chapter": "Search Commands",
  "subtopic": "highlight",
  "category": "Distributable Streaming",
  "source_page": 545,
  "question": "...",
  "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "correct_answer": "B",
  "explanation": "..."
}
```

How it was built:

- Generated with Claude from the **Splunk Enterprise Search Reference 10.4.0** manual, allocated across topics in proportion to how much of the manual each topic occupies
- Reviewed by an LLM pass against the source text for ambiguity and factual accuracy
- Reworked so that **questions stand on their own**: nothing refers to "the manual" or to an example you cannot see, and scenario questions include the data they need
- Balanced so the **correct answers are spread evenly** across A, B, C and D (625 each) and the **correct answer is not systematically the longest or shortest option**

## Categories

The quiz app uses the `category` field:

| Category | Notes |
|---|---|
| Distributable Streaming, Centralized Streaming, Transforming, Generating, Orchestrating, Dataset Processing | The six SPL command types, applied to the "Search Commands" chapter |
| Evaluation Functions | eval functions |
| Statistical and Charting Functions | stats/chart/timechart functions |
| Quick Reference | command reference and SQL-to-SPL material |
| Time Format Variables and Modifiers | strftime variables and time modifiers |
| Internal Commands | commands intended for internal use |
| Introduction | SPL fundamentals |
| Search in the CLI | CLI search options |

For the command types, 90 of the 154 commands take their type from the manual's command-type tables. The other 64 are not in those tables and were assigned from general Splunk knowledge. The full mapping, with a column showing which is which, is in `work/command_types.csv`. Commands that fit several types are filed under their default or primary type. If you disagree with any assignment, edit the CSV and rebuild.

To use a much finer split (one category per command or function group, about 190), rebuild with `--category-field subtopic`.

## Repository layout

```
splunk-foo-quiz/
  bin/build_lookup.py              converts the question JSON to the questions CSV
  default/
    app.conf
    commands.conf                  [outputlookup] is_risky = false
    transforms.conf                lookup definitions for the two CSVs
    data/ui/nav/default.xml
    data/ui/views/
      spl_foo_quiz.xml             Dashboard Studio quiz view
      spl_foo_leaderboard.xml      Dashboard Studio leaderboard view
  lookups/
    spl_quiz_questions.csv         2,500 questions (generated)
    spl_quiz_results.csv           answer log (header only when shipped)
  metadata/default.meta            exported system-wide; write for admin, power, user
  README/                          notes and pasteable view definitions
splunk_mcq_questions.json          the source question bank
splunk-foo-quiz.tar.gz             installable package
```

## Rebuilding the questions lookup

After editing the question JSON, regenerate the CSV and repackage:

```bash
python3 splunk-foo-quiz/bin/build_lookup.py splunk_mcq_questions.json
tar -czf splunk-foo-quiz.tar.gz splunk-foo-quiz/
```

`build_lookup.py` accepts a JSON array or NDJSON, and options either as `{"A": ...}` or `["A) ...", ...]`. It strips any `A)`-style prefixes, upper-cases `correct_answer`, and fails on duplicate ids or a malformed answer.

## Resetting scores

Run this search once as an admin to clear all answers:

```spl
| makeresults | where 1==0
| table user qid category selected correct_answer is_correct answered_time
| outputlookup spl_quiz_results
```

## Design notes and known limitations

- **Concurrent users share one CSV.** Two people answering at exactly the same moment can race on the file rewrite. That is fine for a team or classroom, and a KV Store collection would be the upgrade if you need it.
- **Skip is not remembered.** *Skip this question* reloads the quiz, so a skipped question can come up again.
- **Identity is the Splunk login.** Scores follow the Splunk user name, so shared accounts share a score.
- **Dashboard Studio quirks.** The dashboards avoid tokens in chain searches and avoid the `|s` filter on multiselect tokens, both of which caused problems on some Studio builds. Table click handlers read the clicked row's `qid`. If a click ever loads the wrong row's question on your build, please open an issue.
- **Grid layout.** Because the views use the grid layout, they are easiest to edit in Edit -> Source rather than the visual editor.

## Question quality

The questions were written and checked by AI against the Splunk documentation, then cleaned up by hand and by script. They have **not been individually verified by a human**, and Splunk behaviour, defaults and command availability change between versions (the source is the 10.4.0 manual). Treat this as a study and training aid and not as an authority. If you find a wrong answer or an ambiguous question, please open an issue with the question id.

## License and attribution

- The app code (dashboards, configuration, `build_lookup.py`) is released under the license in `LICENSE` (add one before publishing, for example MIT or Apache-2.0).
- The questions are derived from the publicly available **Splunk Enterprise Search Reference** documentation. They are original questions and explanations, but the underlying facts come from Splunk's documentation, which is copyright Splunk Inc. This project is not affiliated with or endorsed by Splunk.
- Splunk is a trademark of Splunk Inc.
