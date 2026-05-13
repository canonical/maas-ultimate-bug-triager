import logging
import time
from typing import Any

from launchpadlib.launchpad import Launchpad

from maas_ultimate_bug_triager.config import LaunchpadConfig
from maas_ultimate_bug_triager.models.bug import (
    Attachment,
    BugDetail,
    BugSummary,
    Comment,
)

logger = logging.getLogger(__name__)


class LaunchpadService:
    CACHE_TTL = 300

    def __init__(
        self,
        config: LaunchpadConfig | None = None,
        lp: Launchpad | None = None,
    ) -> None:
        if lp is not None:
            self.lp = lp
            self.config = config or LaunchpadConfig()
        elif config is not None and config.oauth_token and config.oauth_token_secret:
            self.config = config
            logger.debug("Logging in to Launchpad...")
            start = time.time()
            self.lp = Launchpad.login(
                config.consumer_key,
                config.oauth_token,
                config.oauth_token_secret,
                service_root="production",
            )
            logger.debug("Launchpad login took %.2fs", time.time() - start)
        else:
            raise ValueError(
                "Either a Launchpad instance or config with"
                " OAuth credentials must be provided"
            )
        logger.debug("Fetching MAAS project...")
        start = time.time()
        self.project = self.lp.projects["maas"]
        logger.debug("Fetched MAAS project in %.2fs", time.time() - start)
        self._cache: dict[str, tuple[float, Any]] = {}

    def _is_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        ts, _ = self._cache[key]
        return (time.time() - ts) < self.CACHE_TTL

    def _set(self, key: str, value: Any) -> None:
        self._cache[key] = (time.time(), value)

    def _invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def _invalidate_prefix(self, prefix: str) -> None:
        keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_remove:
            del self._cache[k]

    def fetch_untriaged_bugs(self) -> list[BugSummary]:
        cache_key = "untriaged_bugs"
        if self._is_valid(cache_key):
            logger.debug("fetch_untriaged_bugs: cache hit")
            return self._cache[cache_key][1]
        logger.debug("fetch_untriaged_bugs: cache miss, querying Launchpad...")
        start = time.time()
        tasks = self.project.searchTasks(status=["New", "Incomplete"])
        logger.debug("searchTasks returned in %.2fs", time.time() - start)
        result: list[BugSummary] = []
        for task in tasks:
            t0 = time.time()
            bug = task.bug
            owner = task.owner
            owner_name = getattr(owner, "display_name", None) or owner.name
            logger.debug("  bug %d fetched in %.2fs", bug.id, time.time() - t0)
            result.append(
                BugSummary(
                    id=bug.id,
                    title=bug.title,
                    status=task.status,
                    importance=task.importance,
                    owner=owner_name,
                    date_created=bug.date_created,
                    tags=list(bug.tags),
                )
            )
        elapsed = time.time() - start
        logger.debug("fetch_untriaged_bugs: %d bugs in %.2fs", len(result), elapsed)
        self._set(cache_key, result)
        return result

    def _get_maas_bug_task(self, bug: Any) -> Any:
        for task in bug.bug_tasks:
            if task.target.name == "maas":
                return task
        return None

    def get_bug_task_url(self, bug_id: int) -> str:
        cache_key = f"bug_task_url:{bug_id}"
        if self._is_valid(cache_key):
            logger.debug("get_bug_task_url(%d): cache hit", bug_id)
            return self._cache[cache_key][1]
        logger.debug("get_bug_task_url(%d): cache miss, fetching...", bug_id)
        start = time.time()
        bug = self.lp.bugs[bug_id]
        task = self._get_maas_bug_task(bug)
        if task is None:
            raise ValueError(f"No MAAS bug task found for bug {bug_id}")
        url = task.self_link
        logger.debug("get_bug_task_url(%d): took %.2fs", bug_id, time.time() - start)
        self._set(cache_key, url)
        return url

    def fetch_bug_details(self, bug_id: int) -> BugDetail:
        cache_key = f"bug_detail:{bug_id}"
        if self._is_valid(cache_key):
            logger.debug("fetch_bug_details(%d): cache hit", bug_id)
            return self._cache[cache_key][1]
        logger.debug("fetch_bug_details(%d): cache miss, fetching...", bug_id)
        start = time.time()
        bug = self.lp.bugs[bug_id]
        logger.debug("  fetched bug object in %.2fs", time.time() - start)
        t0 = time.time()
        task = self._get_maas_bug_task(bug)
        logger.debug("  fetched bug task in %.2fs", time.time() - t0)
        owner = task.owner
        owner_name = getattr(owner, "display_name", None) or owner.name
        comments: list[Comment] = []
        t0 = time.time()
        for i, msg in enumerate(bug.messages):
            if i == 0:
                continue
            msg_owner = msg.owner
            msg_owner_name = getattr(msg_owner, "display_name", None) or msg_owner.name
            comments.append(
                Comment(
                    author=msg_owner_name,
                    date=msg.date_created,
                    content=msg.content,
                )
            )
        logger.debug("  fetched %d comments in %.2fs", len(comments), time.time() - t0)
        attachments: list[Attachment] = []
        t0 = time.time()
        for att in bug.attachments:
            attachments.append(
                Attachment(
                    id=int(att.self_link.split("/")[-1]),
                    title=att.title,
                    content_type=getattr(att, "type", None),
                    size=None,
                )
            )
        logger.debug(
            "  fetched %d attachments in %.2fs",
            len(attachments),
            time.time() - t0,
        )
        detail = BugDetail(
            id=bug.id,
            title=bug.title,
            status=task.status,
            importance=task.importance,
            owner=owner_name,
            date_created=bug.date_created,
            tags=list(bug.tags),
            description=bug.description,
            comments=comments,
            attachments=attachments,
        )
        logger.debug("fetch_bug_details(%d): total %.2fs", bug_id, time.time() - start)
        self._set(cache_key, detail)
        return detail

    def add_comment(self, bug_id: int, message: str) -> None:
        logger.debug("add_comment(%d): starting...", bug_id)
        start = time.time()
        bug = self.lp.bugs[bug_id]
        bug.newMessage(content=message)
        logger.debug("add_comment(%d): took %.2fs", bug_id, time.time() - start)
        self._invalidate(f"bug_detail:{bug_id}")
        self._invalidate("untriaged_bugs")

    def set_status(self, bug_task_url: str, status: str) -> None:
        logger.debug("set_status(%s, %s): starting...", bug_task_url, status)
        start = time.time()
        bug_task = self.lp.load(bug_task_url)
        logger.debug("  loaded bug task in %.2fs", time.time() - start)
        bug_task.status = status
        t0 = time.time()
        bug_task.lp_save()
        logger.debug("  saved in %.2fs", time.time() - t0)
        logger.debug("set_status: total %.2fs", time.time() - start)
        self._invalidate_prefix("bug_detail:")
        self._invalidate("untriaged_bugs")

    def add_tag(self, bug_id: int, tag: str) -> None:
        logger.debug("add_tag(%d, %s): starting...", bug_id, tag)
        start = time.time()
        bug = self.lp.bugs[bug_id]
        bug.tags = bug.tags + [tag]
        bug.lp_save()
        logger.debug("add_tag(%d): took %.2fs", bug_id, time.time() - start)
        self._invalidate(f"bug_detail:{bug_id}")
        self._invalidate("untriaged_bugs")

    def remove_tag(self, bug_id: int, tag: str) -> None:
        logger.debug("remove_tag(%d, %s): starting...", bug_id, tag)
        start = time.time()
        bug = self.lp.bugs[bug_id]
        bug.tags = [t for t in bug.tags if t != tag]
        bug.lp_save()
        logger.debug("remove_tag(%d): took %.2fs", bug_id, time.time() - start)
        self._invalidate(f"bug_detail:{bug_id}")
        self._invalidate("untriaged_bugs")

    def set_importance(self, bug_task_url: str, importance: str) -> None:
        logger.debug("set_importance(%s, %s): starting...", bug_task_url, importance)
        start = time.time()
        bug_task = self.lp.load(bug_task_url)
        logger.debug("  loaded bug task in %.2fs", time.time() - start)
        bug_task.importance = importance
        t0 = time.time()
        bug_task.lp_save()
        logger.debug("  saved in %.2fs", time.time() - t0)
        logger.debug("set_importance: total %.2fs", time.time() - start)
        self._invalidate_prefix("bug_detail:")
        self._invalidate("untriaged_bugs")
