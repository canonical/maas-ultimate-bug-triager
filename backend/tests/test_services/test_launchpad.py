from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from maas_ultimate_bug_triager.config import LaunchpadConfig
from maas_ultimate_bug_triager.models.bug import BugDetail, BugSummary
from maas_ultimate_bug_triager.services.launchpad import LaunchpadService


@pytest.fixture
def mock_lp():
    lp = MagicMock()
    project = MagicMock()
    lp.projects.__getitem__.return_value = project
    return lp, project


@pytest.fixture
def service(mock_lp):
    lp, project = mock_lp
    config = LaunchpadConfig(
        oauth_token="t", oauth_token_secret="s", consumer_key="ck"
    )
    svc = LaunchpadService(config=config, lp=lp)
    return svc, lp, project


def _make_bug_task(
    bug_id,
    title,
    status,
    importance,
    owner_name,
    date_created,
    tags,
    description="",
    messages=None,
    attachments=None,
    bug_tasks=None,
):
    bug = MagicMock()
    bug.id = bug_id
    bug.title = title
    bug.date_created = date_created
    bug.tags = list(tags)
    bug.description = description
    bug.messages = messages or []
    bug.attachments = attachments or []
    bug.newMessage = MagicMock()

    owner = MagicMock()
    owner.display_name = owner_name
    owner.name = owner_name.lower().replace(" ", "")

    task = MagicMock()
    task.bug = bug
    task.status = status
    task.importance = importance
    task.owner = owner
    task.self_link = f"https://api.launchpad.net/1.0/maas/+bug/{bug_id}"
    task.target = MagicMock()
    task.target.name = "maas"

    maas_task = task

    if bug_tasks is not None:
        task.bug.bug_tasks = bug_tasks
    else:
        task.bug.bug_tasks = [maas_task]

    return task, bug, owner


def test_fetch_untriaged_bugs_returns_correct_list(service):
    svc, lp, project = service
    dt1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    dt2 = datetime(2025, 2, 1, tzinfo=timezone.utc)
    task1, bug1, owner1 = _make_bug_task(
        1, "Bug One", "New", "Undecided", "Alice", dt1, ["tag1"]
    )
    task2, bug2, owner2 = _make_bug_task(
        2,
        "Bug Two",
        "Incomplete (with response)",
        "Medium",
        "Bob",
        dt2,
        ["tag2", "tag3"],
    )
    project.searchTasks.return_value = [task1, task2]

    result = svc.fetch_untriaged_bugs()

    assert len(result) == 2
    assert result[0] == BugSummary(
        id=1,
        title="Bug One",
        status="New",
        importance="Undecided",
        owner="Alice",
        date_created=dt1,
        tags=["tag1"],
    )
    assert result[1] == BugSummary(
        id=2,
        title="Bug Two",
        status="Incomplete (with response)",
        importance="Medium",
        owner="Bob",
        date_created=dt2,
        tags=["tag2", "tag3"],
    )
    project.searchTasks.assert_called_once_with(
        status=["New", "Incomplete (with response)"]
    )


def test_fetch_untriaged_bugs_uses_cache(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, _, _ = _make_bug_task(1, "Bug", "New", "Low", "Alice", dt, [])
    project.searchTasks.return_value = [task]

    result1 = svc.fetch_untriaged_bugs()
    result2 = svc.fetch_untriaged_bugs()

    assert result1 == result2
    assert project.searchTasks.call_count == 1


def test_fetch_bug_details_returns_full_detail(service):
    svc, lp, project = service
    dt = datetime(2025, 3, 1, tzinfo=timezone.utc)
    msg_dt = datetime(2025, 3, 2, tzinfo=timezone.utc)

    desc_owner = MagicMock()
    desc_owner.display_name = "Alice"
    desc_owner.name = "alice"

    desc_msg = MagicMock()
    desc_msg.owner = desc_owner
    desc_msg.date_created = dt
    desc_msg.content = "Bug description"

    msg_owner = MagicMock()
    msg_owner.display_name = "Commenter"
    msg_owner.name = "commenter"

    msg = MagicMock()
    msg.owner = msg_owner
    msg.date_created = msg_dt
    msg.content = "This is a comment"

    att = MagicMock()
    att.self_link = "https://api.launchpad.net/1.0/bugs/10/+attachment/42"
    att.title = "screenshot.png"
    att.type = "image/png"

    task, bug, owner = _make_bug_task(
        10,
        "Detail Bug",
        "New",
        "High",
        "Alice",
        dt,
        ["tag-a"],
        description="Bug description",
        messages=[desc_msg, msg],
        attachments=[att],
    )

    lp.bugs.__getitem__.return_value = bug

    result = svc.fetch_bug_details(10)

    assert isinstance(result, BugDetail)
    assert result.id == 10
    assert result.title == "Detail Bug"
    assert result.status == "New"
    assert result.importance == "High"
    assert result.owner == "Alice"
    assert result.description == "Bug description"
    assert result.tags == ["tag-a"]
    assert len(result.comments) == 1
    assert result.comments[0].author == "Commenter"
    assert result.comments[0].content == "This is a comment"
    assert len(result.attachments) == 1
    assert result.attachments[0].id == 42
    assert result.attachments[0].title == "screenshot.png"
    assert result.attachments[0].content_type == "image/png"


def test_fetch_bug_details_uses_cache(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        5, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    lp.bugs.__getitem__.return_value = bug

    result1 = svc.fetch_bug_details(5)
    result2 = svc.fetch_bug_details(5)

    assert result1 == result2
    assert lp.bugs.__getitem__.call_count == 1


def test_add_comment_calls_newMessage_and_invalidates(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        7, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    lp.bugs.__getitem__.return_value = bug

    svc.fetch_bug_details(7)
    assert svc._is_valid("bug_detail:7")

    svc.add_comment(7, "New comment")

    bug.newMessage.assert_called_once_with(content="New comment")
    assert not svc._is_valid("bug_detail:7")


def test_add_comment_invalidates_untriaged_cache(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        7, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    lp.bugs.__getitem__.return_value = bug
    project.searchTasks.return_value = [task]

    svc.fetch_untriaged_bugs()
    assert svc._is_valid("untriaged_bugs")

    svc.add_comment(7, "New comment")

    assert not svc._is_valid("untriaged_bugs")


def test_set_status_calls_lp_save_and_invalidates(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        3, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    lp.bugs.__getitem__.return_value = bug

    bug_task_mock = MagicMock()
    lp.load.return_value = bug_task_mock

    svc.fetch_bug_details(3)
    assert svc._is_valid("bug_detail:3")

    svc.set_status("https://api.launchpad.net/1.0/maas/+bug/3", "Triaged")

    lp.load.assert_called_once_with(
        "https://api.launchpad.net/1.0/maas/+bug/3"
    )
    assert bug_task_mock.status == "Triaged"
    bug_task_mock.lp_save.assert_called_once()
    assert not svc._is_valid("bug_detail:3")
    assert not svc._is_valid("untriaged_bugs")


def test_add_tag_modifies_tags_and_calls_lp_save(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        4, "Bug", "New", "Low", "Alice", dt, ["existing"], description="d"
    )
    lp.bugs.__getitem__.return_value = bug

    svc.fetch_bug_details(4)
    assert svc._is_valid("bug_detail:4")

    svc.add_tag(4, "new-tag")

    assert bug.tags == ["existing", "new-tag"]
    bug.lp_save.assert_called_once()
    assert not svc._is_valid("bug_detail:4")
    assert not svc._is_valid("untriaged_bugs")


def test_remove_tag_modifies_tags_and_calls_lp_save(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        4,
        "Bug",
        "New",
        "Low",
        "Alice",
        dt,
        ["keep", "remove-me"],
        description="d",
    )
    lp.bugs.__getitem__.return_value = bug

    svc.fetch_bug_details(4)
    svc.remove_tag(4, "remove-me")

    assert bug.tags == ["keep"]
    bug.lp_save.assert_called_once()
    assert not svc._is_valid("bug_detail:4")
    assert not svc._is_valid("untriaged_bugs")


def test_set_importance_calls_lp_save(service):
    svc, lp, project = service
    bug_task_mock = MagicMock()
    lp.load.return_value = bug_task_mock

    svc.set_importance("https://api.launchpad.net/1.0/maas/+bug/1", "Critical")

    lp.load.assert_called_once_with(
        "https://api.launchpad.net/1.0/maas/+bug/1"
    )
    assert bug_task_mock.importance == "Critical"
    bug_task_mock.lp_save.assert_called_once()


def test_set_importance_invalidates_cache(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        6, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    lp.bugs.__getitem__.return_value = bug

    svc.fetch_bug_details(6)
    assert svc._is_valid("bug_detail:6")

    bug_task_mock = MagicMock()
    lp.load.return_value = bug_task_mock
    svc.set_importance("https://api.launchpad.net/1.0/maas/+bug/6", "High")

    assert not svc._is_valid("bug_detail:6")
    assert not svc._is_valid("untriaged_bugs")


def test_cache_ttl_expired_entry_not_returned(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        1, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    lp.bugs.__getitem__.return_value = bug

    result1 = svc.fetch_bug_details(1)
    assert lp.bugs.__getitem__.call_count == 1

    svc._cache["bug_detail:1"] = (time.time() - svc.CACHE_TTL - 1, result1)

    result2 = svc.fetch_bug_details(1)
    assert lp.bugs.__getitem__.call_count == 2
    assert result2 == result1


def test_cache_invalidation_removes_entry(service):
    svc, _, _ = service
    svc._set("bug_detail:99", "data")
    assert svc._is_valid("bug_detail:99")
    svc._invalidate("bug_detail:99")
    assert not svc._is_valid("bug_detail:99")


def test_cache_invalidation_prefix_removes_matching_entries(service):
    svc, _, _ = service
    svc._set("bug_detail:1", "a")
    svc._set("bug_detail:2", "b")
    svc._set("untriaged_bugs", "c")
    svc._invalidate_prefix("bug_detail:")
    assert not svc._is_valid("bug_detail:1")
    assert not svc._is_valid("bug_detail:2")
    assert svc._is_valid("untriaged_bugs")


def test_get_bug_task_url_returns_self_link(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        8, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    lp.bugs.__getitem__.return_value = bug

    url = svc.get_bug_task_url(8)
    assert url == "https://api.launchpad.net/1.0/maas/+bug/8"


def test_get_bug_task_url_caches_result(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, _ = _make_bug_task(
        8, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    lp.bugs.__getitem__.return_value = bug

    url1 = svc.get_bug_task_url(8)
    url2 = svc.get_bug_task_url(8)

    assert url1 == url2
    assert lp.bugs.__getitem__.call_count == 1


def test_get_bug_task_url_raises_if_no_maas_task(service):
    svc, lp, project = service
    bug = MagicMock()
    bug.bug_tasks = []
    lp.bugs.__getitem__.return_value = bug

    with pytest.raises(ValueError, match="No MAAS bug task found"):
        svc.get_bug_task_url(99)


def test_fetch_bug_details_owner_display_name_fallback(service):
    svc, lp, project = service
    dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    task, bug, owner = _make_bug_task(
        11, "Bug", "New", "Low", "Alice", dt, [], description="d"
    )
    owner.display_name = None
    owner.name = "alice_user"
    lp.bugs.__getitem__.return_value = bug

    result = svc.fetch_bug_details(11)
    assert result.owner == "alice_user"
