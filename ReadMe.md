# Email Thread Classifier

A lightweight CLI for classifying email threads using bilingual (English/Vietnamese) **rule-based** logic.  
Designed for **PCACS - Second Round Requirements**.

---

## 🔧 Features

- **Input**: JSON containing `thread.subject` and `thread.messages`.
- **Output**: JSON containing `thread_id` (SHA-1 hash) + `label` across multiple schemes.
- **Bilingual**: Precompiled regex rules in English & Vietnamese.
- **O(n)** complexity: In-memory processing only.  
  No network calls. No ML dependencies.
- **Two CLI modes**:  
  - **Arguments** (`--in`, `--out`)  
  - **Interactive** (no arguments, guided menu)

---

## 📦 Installation

```sh
git clone https://github.com/JutsuKKaisen/PAC-CS_Email_Classifier.git
cd PAC-CS_Email_Classifier
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

```

----------

## ▶️ Usage

### 1) Command Line

```sh
python email_classifier/classify_thread.py --in tests/thread.json --out pred.json

```

-   `--in`: path to input JSON file (or `-` to read from STDIN).
    
-   `--out`: path to output JSON file (omit → print to STDOUT).
    

### 2) Interactive Mode

```sh
python email_classifier/classify_thread.py

```

Menu:

1.  Classify from file
    
2.  Paste JSON to classify
    
3.  Exit
    

----------

## 📄 Input/Output Example (from repository data)

### Input (`tests/thread.json`)

```json
{
  "thread": {
    "subject": "Project Ghost",
    "messages": [
      {
        "timestamp": "1999-12-15 07:08:00.000",
        "from": "Sara Shackleton",
        "to": ["Marie Heard"],
        "body": "This is scheduled to close on Friday (don't know what time). ..."
      },
      {
        "timestamp": "1999-12-15 07:14:00.000",
        "from": "Sara Shackleton",
        "to": ["Rod Nelson"],
        "body": "Are you OK with this deal?  I may have a few questions. ..."
      },
      {
        "timestamp": "1999-12-15 09:04:00.000",
        "from": "Sara Shackleton",
        "to": ["Morris Richard Clark", "Stephen H Douglas", "Rhett Jackson"],
        "body": "I don't know who's working on this deal, so I'm forwarding docs to you all ..."
      },
      {
        "timestamp": "1999-12-15 10:22:00.000",
        "from": "Sara Shackleton",
        "to": ["Brenda L Funk", "Craig Clark", "Gareth Bahlmann"],
        "body": "Please confirm the Enron Corp. account for the swap: Citibank ..."
      }
    ]
  }
}

```

### Output (`tests/pred.json`)

```json
{
  "thread_id": "5d1681cc8085f38fa6351b7f5ef3ca42dc8914e6",
  "label": {
    "request_type": "SCHEDULE/MEET",
    "urgency": "URGENT-24H",
    "thread_state": "FOLLOW-UP",
    "scheduling": "PROPOSED_TIME",
    "attachments": [
      "ATTACHED"
    ],
    "tone": "POSITIVE"
  }
}

```

----------

## 🧠 How It Works (Flow Diagram)

```
+---------------------+         +-------------------------+         +-------------------+
|  Input JSON         |         |  classify_thread.py     |         |  rules.py         |
|  (thread.subject,   |  read   |  - normalize_thread()   |  text   |  - regex rules    |
|   thread.messages)  +-------->+  - sort_messages()      +-------->+  - classify_labels|
|                     |         |  - compute_thread_id()  | labels  |    (EN + VI)      |
+----------+----------+         |  - classify_labels()    |         +---------+---------+
           |                    +-----------+-------------+                   |
           |                                 result                          |
           |                                  (dict)                         |
           v                                                                   
+---------------------+                                              +--------------------+
| Example:            |                                              | Example:           |
| tests/thread.json   |                                              | tests/pred.json    |
+---------------------+                                              +--------------------+

```

**Step-by-step process:**

1.  **normalize_thread()** ensures subject and messages are well-formed (fills missing fields).
    
2.  **sort_messages()** orders messages by `timestamp`.
    
3.  **compute_thread_id()** builds SHA-1 hash from `subject + first_ts + last_ts`.
    
4.  **classify_labels()** applies regex-based rules:
    
    -   **Scheduling** precedence: `CONFIRMED > RESCHEDULE > PROPOSED > NONE`.
        
    -   **Request type**: prioritizes meeting-related intent.
        
    -   **Attachments**: detects `ATTACHED`, `EXPECTING_ATTACHMENT`, or `NONE_MENTIONED`.
        
    -   **Urgency**: `URGENT-24H`, `STD-48H`, `LOW-120H`.
        
    -   **Tone**: last message takes priority; fallback = last 3 messages.
        
    -   **Thread state**: `RESOLVED`, `FOLLOW-UP`, or `NEW`.
        

----------

## 🏷️ Label Schemes

-   **request_type**: `EDIT/REVISE | PROVIDE_DOCS | REVIEW/APPROVE | SCHEDULE/MEET | INFO_ONLY`
    
-   **urgency**: `URGENT-24H | STD-48H | LOW-120H`
    
-   **thread_state**: `NEW | FOLLOW-UP | RESOLVED`
    
-   **scheduling**: `PROPOSED_TIME | CONFIRMED_TIME | RESCHEDULE | NO_MEETING`
    
-   **attachments**: `[ATTACHED | EXPECTING_ATTACHMENT | NONE_MENTIONED]`
    
-   **tone**: `POSITIVE | NEUTRAL | FRUSTRATED`
    

----------

## 🧪 Testing

```sh
pytest -q

```

----------

## 📂 Project Structure

```
PAC-CS_Email_Classifier/
├── email_classifier/
│   ├── classify_thread.py      # CLI + Interactive + pipeline (entry point)
│   └── rules.py                # Bilingual rule engine (regex precompiled)
│
├── tests/
│   ├── thread.json             # Sample input (Enron thread: Project Ghost)
│   ├── pred.json               # Sample output (classifier result)
│   └── sample_email_dataset-main/
│       ├── README.md
│       └── sample.json
│
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── context.md                  # Project context / documentation

```
---
Made with ❤️ by /JutsuKKaisen