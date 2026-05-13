from dataclasses import dataclass
from datetime import datetime
from typing import Generator, List, Optional

from launchpadlib.launchpad import Launchpad


@dataclass
class BugMessage:
    owner_display_name: str
    date_created: datetime
    content: str


@dataclass
class BugReport:
    id: int
    title: str
    status: str
    importance: str
    assignee: Optional[str]
    web_link: str
    description: Optional[str]
    messages: List[BugMessage]


def get_launchpad_instance() -> Launchpad:
    return Launchpad.login_with("MAAS Bug Triager", "production")


def get_bug_by_id(lp: Launchpad, bug_id: int) -> BugReport:
    """Fetch a single bug by its Launchpad bug ID and return it as a BugReport."""
    bug = lp.bugs[bug_id]  # type: ignore
    bug_task = bug.bug_tasks[0]

    assignee_name: Optional[str]
    if bug_task.assignee is None:
        assignee_name = None
    else:
        assignee_name = bug_task.assignee.display_name or str(bug_task.assignee)

    messages: List[BugMessage] = []
    if bug.messages:
        for message in bug.messages:
            owner_display = (
                message.owner.display_name
                if message.owner is not None
                else str(message.owner)
            )
            messages.append(
                BugMessage(
                    owner_display_name=owner_display,
                    date_created=message.date_created,
                    content=message.content,
                )
            )

    return BugReport(
        id=int(bug.id),
        title=str(bug.title),
        status=str(bug_task.status),
        importance=str(bug_task.importance),
        assignee=assignee_name,
        web_link=str(bug.web_link),
        description=str(bug.description) if bug.description else None,
        messages=messages,
    )


def get_untriaged_bugs(lp: Launchpad) -> Generator[BugReport, None, None]:
    """Return a list of untriaged MAAS bugs as structured dataclasses."""
    maas = lp.projects["maas"]  # type: ignore

    for bug_task in maas.searchTasks(status="New"):
        bug = bug_task.bug

        # Assignee might be None or an object; capture a displayable name.
        assignee_name: Optional[str]
        if bug_task.assignee is None:
            assignee_name = None
        else:
            assignee_name = bug_task.assignee.display_name or str(bug_task.assignee)

        # Collect messages, if any
        messages: List[BugMessage] = []
        if bug.messages:
            for message in bug.messages:
                owner_display = (
                    message.owner.display_name
                    if message.owner is not None
                    else str(message.owner)
                )
                messages.append(
                    BugMessage(
                        owner_display_name=owner_display,
                        date_created=message.date_created,
                        content=message.content,
                    )
                )

            yield BugReport(
                id=int(bug.id),
                title=str(bug.title),
                status=str(bug_task.status),
                importance=str(bug_task.importance),
                assignee=assignee_name,
                web_link=str(bug.web_link),
                description=str(bug.description) if bug.description else None,
                messages=messages,
            )
