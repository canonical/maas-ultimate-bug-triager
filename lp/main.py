from launchpadlib.launchpad import Launchpad


def main():
    # Connect to Launchpad (will use existing credentials or prompt for new ones)
    lp = Launchpad.login_with("MAAS Bug Triager", "production")

    maas = lp.projects["maas"]  # type: ignore

    untriaged_bugs = maas.searchTasks(status="New")

    print(f"Found {len(untriaged_bugs)} untriaged bugs in MAAS\n")

    for bug_task in untriaged_bugs:
        bug = bug_task.bug
        print(f"Bug #{bug.id}: {bug.title}")
        print(f"  Status: {bug_task.status}")
        print(f"  Importance: {bug_task.importance}")
        print(f"  Assigned to: {bug_task.assignee}")
        print(f"  URL: {bug.web_link}")
        print()

        # Get bug report description/contents
        if bug.description:
            print("  Description:")
            print(f"  {bug.description}")
            print()

        # Get bug messages (comments)
        if bug.messages:
            print(f"  Messages ({len(bug.messages)}):")
            for i, message in enumerate(bug.messages, 1):
                print(
                    f"    [{i}] {message.owner.display_name} - {message.date_created}"
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
