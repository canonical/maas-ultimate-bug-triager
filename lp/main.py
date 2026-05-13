from lp.bugs import get_launchpad_instance, get_untriaged_bugs


def main():
    # Connect to Launchpad (will use existing credentials or prompt for new ones)
    lp = get_launchpad_instance()

    bug_reports = get_untriaged_bugs(lp)
    print(f"Found {len(bug_reports)} untriaged bugs in MAAS\n")

    for br in bug_reports:
        print(f"Bug #{br.id}: {br.title}")
        print(f"  Status: {br.status}")
        print(f"  Importance: {br.importance}")
        print(f"  Assigned to: {br.assignee}")
        print(f"  URL: {br.web_link}")
        print()

        # Bug report description/contents
        if br.description:
            print("  Description:")
            print(f"  {br.description}")
            print()

        # Bug messages (comments)
        if br.messages:
            print(f"  Messages ({len(br.messages)}):")
            for i, message in enumerate(br.messages, 1):
                print(
                    f"    [{i}] {message.owner_display_name} - {message.date_created}"
                )
                content_preview = (
                    message.content[:200]
                    if len(message.content) > 200
                    else message.content
                )
                print(f"        {content_preview}")
                if len(message.content) > 200:
                    print("        ...")
            print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
