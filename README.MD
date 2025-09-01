# Email Thread Classifier

A lightweight CLI tool for classifying email threads using bilingual (EN/VI) rule-based logic. Designed for operational use in the PCACS - Second Round Requirements.

## Features

- **Input**: Accepts a JSON object with `thread.subject` and `thread.messages`.
- **Output**: JSON with `thread_id` and `label` (multi-scheme classification).
- **Bilingual**: Supports English and Vietnamese keywords.
- **Fast**: All operations are O(n), in-memory, no external API calls.
- **CLI & Interactive**: Run from command line or interactively.

## Installation

Clone the repository and (optionally) create a virtual environment:

```sh
git clone <your-repo-url>
cd PAC-CS_Email_Classifier
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Command Line

```sh
python email_classifier/classify_thread.py --in tests/sample.json --out pred.json
```

- `--in`: Path to input JSON file (or `-` for STDIN).
- `--out`: Path to output JSON file (or STDOUT if omitted).

### Interactive Mode

```sh
python email_classifier/classify_thread.py
```

Follow prompts to classify from file or paste JSON.

## Input Format

```json
{
  "thread": {
    "subject": "Re: Project kickoff",
    "messages": [
      {"timestamp": "2025-09-01 09:00:00.000", "from": "a@x", "to": ["b@y"], "body": "Let's meet Tue 3pm?"},
      {"timestamp": "2025-09-01 10:15:12.000", "from": "b@y", "to": ["a@x"], "body": "Confirmed. See you at 15:00, sending Zoom link. Thanks!"}
    ]
  }
}
```

## Output Format

```json
{
  "thread_id": "<sha1>",
  "label": {
    "request_type": "SCHEDULE/MEET",
    "urgency": "STD-48H",
    "thread_state": "FOLLOW-UP",
    "scheduling": "CONFIRMED_TIME",
    "attachments": ["NONE_MENTIONED"],
    "tone": "POSITIVE"
  }
}
```

## Label Schemes

- **request_type**: EDIT/REVISE | PROVIDE_DOCS | REVIEW/APPROVE | SCHEDULE/MEET | INFO_ONLY
- **urgency**: URGENT-24H | STD-48H | LOW-120H
- **thread_state**: NEW | FOLLOW-UP | RESOLVED
- **scheduling**: PROPOSED_TIME | CONFIRMED_TIME | RESCHEDULE | NO_MEETING
- **attachments**: [ATTACHED | EXPECTING_ATTACHMENT | NONE_MENTIONED]
- **tone**: POSITIVE | NEUTRAL | FRUSTRATED

## Testing

Run unit tests with:

```sh
pytest -q
```

## Project Structure

```
email_classifier/
  classify_thread.py
  rules.py
tests/
  sample.json
  test.json
  sample_email_dataset-main/
    README.md
    sample.json
requirements.txt
.gitignore
context.md
```

---

For details on the rule logic, see [`email_classifier/rules.py`](email_classifier/rules.py).
