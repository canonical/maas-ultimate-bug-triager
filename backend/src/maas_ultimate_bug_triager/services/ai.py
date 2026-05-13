from __future__ import annotations

import asyncio
import json
import logging
import time

import httpx
from google import genai
from google.genai.types import GenerateContentConfig

from maas_ultimate_bug_triager.config import AIConfig
from maas_ultimate_bug_triager.models.action import AnalysisResponse
from maas_ultimate_bug_triager.models.bug import BugDetail

logger = logging.getLogger(__name__)

BUG_REPORTING_GUIDELINES_URL = (
    "https://raw.githubusercontent.com/canonical/maas/refs/heads/master"
    "/docs/uncategorized/report-a-bug.md"
)

_SYSTEM_INSTRUCTION = (
    "You are a MAAS bug triager. Analyze the bug report and suggest triage actions. "
    "Respond with valid JSON matching the specified schema."
)

_VALID_STATUSES = "New, Incomplete, Triaged, Invalid, Won't Fix, Opinion, Confirmed"
_VALID_IMPORTANCES = "Undecided, Low, Medium, High, Critical, Wishlist"

_PROMPT_TEMPLATE = (
    "You are a MAAS (Metal as a Service) bug triager for Canonical's "
    "MAAS project.\n"
    "\n"
    "Analyze the following bug report and suggest actions to triage it. "
    "The bug is in the \"{bug_status}\" state and needs triaging. "
    "Always suggest a status and importance to set.\n"
    "\n"
    "## MAAS Bug Reporting Guidelines\n"
    "Use these guidelines to evaluate the quality of the bug report:\n"
    "{bug_reporting_guidelines}\n"
    "If you need to point the reporter to these guidelines, refer them to: "
    "https://canonical.com/maas/docs/how-to-report-and-review-bugs\n"
    "\n"
    "## Bug Report\n"
    "- **ID**: {bug_id}\n"
    "- **Title**: {bug_title}\n"
    "- **Status**: {bug_status}\n"
    "- **Importance**: {bug_importance}\n"
    "- **Reporter**: {bug_owner}\n"
    "- **Created**: {bug_date_created}\n"
    "- **Tags**: {bug_tags}\n"
    "\n"
    "## Description\n"
    "{bug_description}\n"
    "\n"
    "## Comments\n"
    "{formatted_comments}\n"
    "\n"
    "## Attachments\n"
    "{formatted_attachments}\n"
    "\n"
    "## Instructions\n"
    "Respond with a JSON object matching this schema:\n"
    "- reasoning: string — your assessment of the bug and why you "
    "suggest these actions\n"
    "- suggested_actions: list of action objects, each with:\n"
    '  - type: "ADD_COMMENT" | "SET_STATUS" | "SET_IMPORTANCE" '
    '| "ADD_TAG" | "REMOVE_TAG"\n'
    "  - Additional fields depend on type:\n"
    "    - ADD_COMMENT: content (string)\n"
    "    - SET_STATUS: status (one of: {_valid_statuses})\n"
    "    - SET_IMPORTANCE: importance (one of: {_valid_importances})\n"
    "    - ADD_TAG: tag (string)\n"
    "    - REMOVE_TAG: tag (string)\n"
    "\n"
    "Always include a SET_STATUS action. Only include a SET_IMPORTANCE "
    "action if you also set the status to Triaged; until a bug is "
    "Triaged the importance should remain unset.\n"
    "\n"
    "Common triage patterns:\n"
    "- If the bug lacks steps to reproduce → set status to "
    "Incomplete, add a comment requesting more info; do not set importance\n"
    "- If the bug is a duplicate → set status to Invalid, add a "
    "comment noting the duplicate; do not set importance\n"
    "- If the bug has clear reproduction steps and seems valid → "
    "set status to Triaged, set appropriate importance\n"
    "- If the bug is about a feature request rather than a bug → "
    'set status to Opinion, add tag "feature-request"; do not set importance\n'
    "- If the bug report is spam or completely irrelevant → "
    "set status to Invalid; do not set importance"
)


def _format_comments(comments: list) -> str:
    if not comments:
        return "No comments."
    lines = []
    for comment in comments:
        lines.append(f"- **{comment.author}** ({comment.date}): {comment.content}")
    return "\n".join(lines)


def _format_attachments(attachments: list) -> str:
    if not attachments:
        return "No attachments."
    return "\n".join(f"- {att.title}" for att in attachments)


def _build_prompt(bug: BugDetail, bug_reporting_guidelines: str) -> str:
    return _PROMPT_TEMPLATE.format(
        bug_id=bug.id,
        bug_title=bug.title,
        bug_status=bug.status,
        bug_importance=bug.importance,
        bug_owner=bug.owner,
        bug_date_created=bug.date_created,
        bug_tags=", ".join(bug.tags) if bug.tags else "None",
        bug_description=bug.description,
        formatted_comments=_format_comments(bug.comments),
        formatted_attachments=_format_attachments(bug.attachments),
        _valid_statuses=_VALID_STATUSES,
        _valid_importances=_VALID_IMPORTANCES,
        bug_reporting_guidelines=bug_reporting_guidelines,
    )


class AIService:
    def __init__(self, config: AIConfig) -> None:
        self.config = config
        self.client = genai.Client(api_key=config.api_key)
        self._bug_reporting_guidelines = self._fetch_bug_reporting_guidelines()

    def _fetch_bug_reporting_guidelines(self) -> str:
        try:
            response = httpx.get(BUG_REPORTING_GUIDELINES_URL, timeout=30)
            response.raise_for_status()
            logger.info("Fetched bug reporting guidelines from %s", BUG_REPORTING_GUIDELINES_URL)
            return response.text
        except Exception:
            logger.warning(
                "Failed to fetch bug reporting guidelines from %s",
                BUG_REPORTING_GUIDELINES_URL,
                exc_info=True,
            )
            return "Guidelines unavailable."

    async def analyze_bug(self, bug: BugDetail) -> AnalysisResponse:
        prompt = _build_prompt(bug, self._bug_reporting_guidelines)
        config = GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=_SYSTEM_INSTRUCTION,
        )
        logger.debug(
            "analyze_bug(%d): calling AI model %s...",
            bug.id,
            self.config.model,
        )
        start = time.time()
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=self.config.model,
                contents=prompt,
                config=config,
            ),
        )
        elapsed = time.time() - start
        logger.debug("analyze_bug(%d): AI responded in %.2fs", bug.id, elapsed)
        parsed = json.loads(response.text)
        parsed["bug_id"] = bug.id
        return AnalysisResponse.model_validate(parsed)

    def set_model(self, model: str) -> None:
        self.config.model = model

    def get_available_models(self) -> list[str]:
        return ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
