import json
from pathlib import Path
from datetime import datetime
from lp.bugs import get_launchpad_instance, get_untriaged_bugs


def serialize_bug_report(br):
    """Convert BugReport dataclass to JSON-serializable dict."""
    messages = []
    if br.messages:
        for msg in br.messages:
            messages.append({
                "owner_display_name": msg.owner_display_name,
                "date_created": msg.date_created.isoformat() if isinstance(msg.date_created, datetime) else str(msg.date_created),
                "content": msg.content
            })
    
    return {
        "id": br.id,
        "title": br.title,
        "status": br.status,
        "importance": br.importance,
        "assignee": br.assignee,
        "web_link": br.web_link,
        "description": br.description,
        "messages": messages
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch untriaged MAAS bugs from Launchpad")
    parser.add_argument("--limit", type=int, default=10,
                        help="Limit number of bugs to fetch (default: 10)")
    parser.add_argument("--output", type=str, default="bugs.json",
                        help="Output JSON file to save bugs (default: bugs.json)")
    args = parser.parse_args()
    
    # Connect to Launchpad (will use existing credentials or prompt for new ones)
    lp = get_launchpad_instance()

    bug_reports = get_untriaged_bugs(lp)
    bug_reports = bug_reports[:args.limit]
    print(f"Found {len(bug_reports)} untriaged bugs in MAAS\n")

    # Serialize and save to JSON
    bugs_data = [serialize_bug_report(br) for br in bug_reports]
    
    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(bugs_data, f, indent=2)
    
    print(f"Saved {len(bugs_data)} bugs to {output_path}\n")
    
    # Also display a summary
    for br in bug_reports:
        print(f"Bug #{br.id}: {br.title}")
        print(f"  Status: {br.status}")
        print(f"  Importance: {br.importance}")
        print(f"  Assigned to: {br.assignee}")
        print(f"  URL: {br.web_link}")
        print(f"  Messages: {len(br.messages) if br.messages else 0}")
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
