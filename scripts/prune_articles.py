#!/usr/bin/env python
import csv, os, sys
from datetime import datetime, timedelta, timezone

def prune_csv(file_path, days):
    """
    Prunes a CSV file by removing rows where the 'Date Added' is older than a specified number of days.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Nothing to prune.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            rows = list(reader)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    if not rows:
        print("No rows to prune.")
        return

    if "Date Added" not in fieldnames:
        print("Warning: 'Date Added' column not found. Cannot prune based on date.")
        return

    kept_rows = []
    pruned_count = 0
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=days)

    for row in rows:
        date_str = row.get("Date Added")
        if not date_str:
            kept_rows.append(row) # Keep rows with no date
            continue
        try:
            # Assuming date is in YYYY-MM-DD format
            row_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if row_date >= cutoff_date:
                kept_rows.append(row)
            else:
                pruned_count += 1
        except ValueError:
            kept_rows.append(row) # Keep rows with malformed dates

    try:
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept_rows)
    except Exception as e:
        print(f"Error writing back to {file_path}: {e}")
        return

    print(f"Pruned {pruned_count} articles older than {days} days from {os.path.basename(file_path)}. {len(kept_rows)} remain.")

def main():
    # Basic command-line argument parsing
    file_path = "data/articles.csv"
    days = 15

    args = sys.argv[1:]
    if "--file" in args:
        try:
            file_path = args[args.index("--file") + 1]
        except IndexError:
            print("Error: --file argument needs a value.")
            sys.exit(1)
    if "--days" in args:
        try:
            days = int(args[args.index("--days") + 1])
        except (IndexError, ValueError):
            print("Error: --days argument needs an integer value.")
            sys.exit(1)

    prune_csv(file_path, days)

if __name__ == "__main__":
    main()
