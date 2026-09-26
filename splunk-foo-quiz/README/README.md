# splunk-foo-quiz

Randomized multiple-choice SPL knowledge quiz plus a per-user leaderboard, built with
Dashboard Studio (`version="2"`) views. Storage is **plain CSV lookups only - no KV Store**.

## Contents
| Path | Purpose |
|---|---|
| `default/data/ui/views/spl_foo_quiz.xml` | Quiz dashboard |
| `default/data/ui/views/spl_foo_leaderboard.xml` | Leaderboard dashboard |
| `lookups/spl_quiz_questions.csv` | 2,500 questions (generated) |
| `lookups/spl_quiz_results.csv` | Answer log (header only when shipped) |
| `bin/build_lookup.py` | Regenerates the questions CSV from the source JSON |
| `default/commands.conf` | `[outputlookup] is_risky = false` so answers save without the risky-command prompt |
| `README/*.studio.json` | Each view's definition JSON, for pasting into **Edit -> Source** |

## Install
**Apps -> Manage Apps -> Install app from file** and upload `splunk-foo-quiz.tar.gz`
(admin or a role with app-install rights). If the views ever need repair without CLI access,
open the dashboard, choose **Edit -> Source**, and paste the matching `README/*.studio.json`.

## Question source and categories
Source file: `splunk_mcq_questions.json` (2,500 questions, ids 1-2500). To rebuild the CSV:

    python3 bin/build_lookup.py /path/to/splunk_mcq_questions.json

The script accepts a JSON array or NDJSON, and options either as `{"A": ...}` or `["A) ...", ...]`
(prefixes stripped, `correct_answer` upper-cased). The quiz *category* is the question's `chapter`
(13 categories: the six command types (Distributable Streaming, Centralized Streaming, Transforming, Generating, Orchestrating, Dataset Processing), Evaluation Functions, Statistical and Charting Functions, Quick Reference,
Internal Commands, Time Format Variables and Modifiers, Introduction, Search in the CLI).
Use `--category-field subtopic` for a much finer split (about 190 categories, one per command/function group).

## How it works
* Identity comes from `$env:user$`. Answers are appended with `| outputlookup append=true spl_quiz_results`.
* Every scoring read collapses re-clicks with `stats latest(is_correct) ... by user qid`.
* The next question is random, restricted to the selected categories, and skips questions the user already answered.
* Multiselect token is used as `"," . "$tok_cats$" . ","` (comma-fenced, no `|s` filter) and matched with `like()`.
* No tokens in `ds.chain` queries; the Choose One table reads `ds_pick_question` directly and shows exactly `choice`, `qid`.

## Reset all scores

    | makeresults | where 1==0
    | table user qid category selected correct_answer is_correct answered_time
    | outputlookup spl_quiz_results

## Post-install check

    | inputlookup spl_quiz_questions | stats count by category
    | inputlookup spl_quiz_results

## Known limits
* Everyone's answers share one CSV; simultaneous submits by different users can race (last writer wins on the file rewrite path Splunk uses for append).
* The Studio JSON was not rendered in a Studio UI while building; if a panel option is rejected by your Splunk version, adjust in Edit -> Source.
