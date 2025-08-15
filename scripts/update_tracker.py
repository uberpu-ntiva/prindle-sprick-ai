#!/usr/bin/env python
import argparse, csv, json
def latest_per_tool(items):
    by={}
    for it in items:
        k=it["tool"]
        if k not in by or it["date"]>by[k]["date"]:
            by[k]=it
    return by
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True, help="Input CSV file for tool tracking")
    ap.add_argument("--log", required=True, help="Input JSON file with news items")
    ap.add_argument("--out", required=True, help="Output CSV file")
    args = ap.parse_args()

    # Load the latest news items
    try:
        with open(args.log, "r", encoding="utf-8") as f:
            log = json.load(f)
        latest = latest_per_tool(log.get("items", []))
    except FileNotFoundError:
        print(f"Log file not found at {args.log}. No statuses will be updated.")
        latest = {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {args.log}. No statuses will be updated.")
        latest = {}

    # Read the tracker CSV, update statuses, and clean the data
    try:
        with open(args.tracker, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Sanitize fieldnames to remove any None keys from blank columns
            original_fields = reader.fieldnames or []
            clean_fields = [field for field in original_fields if field is not None]

            if "Status" not in clean_fields:
                clean_fields.append("Status")

            updated_rows = []
            for row in reader:
                # Create a new row dictionary, filtering out the None key if it exists
                clean_row = {k: v for k, v in row.items() if k is not None}

                tool_name = clean_row.get("Tool")
                if tool_name:
                    latest_item = latest.get(tool_name)
                    if latest_item:
                        clean_row["Status"] = f'{latest_item.get("severity", "Minor")}: {latest_item.get("headline", "")} ({latest_item.get("date", "")})'

                updated_rows.append(clean_row)
    except FileNotFoundError:
        print(f"Tracker file not found at {args.tracker}. Cannot proceed.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading {args.tracker}: {e}")
        return

    # Write the cleaned and updated data back to the output file
    try:
        with open(args.out, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=clean_fields)
            writer.writeheader()
            writer.writerows(updated_rows)
        print(f"Successfully updated tracker status and wrote to {args.out}.")
    except Exception as e:
        print(f"An unexpected error occurred while writing to {args.out}: {e}")

if __name__ == "__main__":
    main()