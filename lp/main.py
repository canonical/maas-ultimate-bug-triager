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
        print()


if __name__ == "__main__":
    main()
