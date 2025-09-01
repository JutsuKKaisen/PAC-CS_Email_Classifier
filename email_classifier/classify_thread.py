import argparse
import sys
import json
import hashlib
import os
from rules import classify_labels

# ---------------- Core helpers ----------------

def normalize_thread(thread):
    subject = (thread or {}).get("subject", "") or ""
    messages = (thread or {}).get("messages", []) or []
    for msg in messages:
        msg.setdefault("timestamp", "")
        msg.setdefault("from", "")
        msg.setdefault("to", [])
        msg.setdefault("body", "")
    return subject, messages


def sort_messages(messages):
    # Python sort là stable, nên khi timestamp trùng sẽ giữ nguyên thứ tự gốc
    return sorted(messages, key=lambda m: m.get("timestamp", "") or "")


def compute_thread_id(subject, messages_sorted):
    first_ts = messages_sorted[0]["timestamp"] if messages_sorted else ""
    last_ts = messages_sorted[-1]["timestamp"] if messages_sorted else ""
    basis = (subject + first_ts + last_ts).encode("utf-8")
    return hashlib.sha1(basis).hexdigest()  # hex lowercase


def classify_thread(data):
    thread = (data or {}).get("thread", {}) or {}
    subject, messages = normalize_thread(thread)
    messages_sorted = sort_messages(messages)
    thread_id = compute_thread_id(subject, messages_sorted)
    label = classify_labels(subject, messages_sorted)
    return {"thread_id": thread_id, "label": label}


# ---------------- CLI (tham số) ----------------

def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="classify_cli.py",
        description="Email Thread Classifier CLI"
    )
    parser.add_argument(
        "--in", dest="input", required=True,
        help="Input JSON file (or '-' for STDIN)"
    )
    parser.add_argument(
        "--out", dest="output", default=None,
        help="Output JSON file (or STDOUT if omitted)"
    )
    return parser.parse_args(argv)


def main_cli(argv):
    """
    Chỉ gọi hàm này khi muốn chạy chế độ CLI có tham số.
    """
    args = parse_args(argv)

    # Read input
    if args.input == "-":
        data = json.load(sys.stdin)
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

    result = classify_thread(data)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()


# ---------------- Interactive ----------------

def interactive_cli():
    print("=== Email Thread Classifier Interactive CLI ===")
    while True:
        print("\nOptions:")
        print("1. Classify from file")
        print("2. Paste JSON to classify")
        print("3. Exit")
        choice = input("Select option [1-3]: ").strip()

        if choice == "1":
            path = input("Enter path to JSON file: ").strip()
            if not os.path.isfile(path):
                print("File not found.")
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                result = classify_thread(data)
                print("\nClassification result:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                save = input("Save result to file? [y/N]: ").strip().lower()
                if save == "y":
                    out_path = input("Enter output file path: ").strip()
                    with open(out_path, "w", encoding="utf-8") as out_f:
                        json.dump(result, out_f, ensure_ascii=False, indent=2)
                    print(f"Result saved to {out_path}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "2":
            print("Paste your thread JSON below (end with an empty line):")
            lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if line.strip() == "":
                    break
                lines.append(line)
            try:
                data = json.loads("\n".join(lines))
                result = classify_thread(data)
                print("\nClassification result:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                save = input("Save result to file? [y/N]: ").strip().lower()
                if save == "y":
                    out_path = input("Enter output file path: ").strip()
                    with open(out_path, "w", encoding="utf-8") as out_f:
                        json.dump(result, out_f, ensure_ascii=False, indent=2)
                    print(f"Result saved to {out_path}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid option.")


# ---------------- Entry point ----------------
if __name__ == "__main__":
    # Nếu có tham số (>=1 sau tên script) → chạy CLI có argparse
    # Nếu không có tham số → chạy interactive, không đòi --in
    if len(sys.argv) > 1:
        # Bỏ phần tên script, chỉ truyền danh sách arg cho parser
        main_cli(sys.argv[1:])
    else:
        interactive_cli()
