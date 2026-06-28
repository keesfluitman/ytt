"""Improve machine translations with a remote Claude Code instance.

The container has no Anthropic API key. Instead it SSHes to a host where the
`claude` CLI is logged in (subscription OAuth) and runs it in headless/print
mode. The whole prompt is sent over stdin so no transcript text ever lands on
the remote shell command line (no escaping/injection surface); the remote
command itself is static.

Design notes:
- Source paragraphs go in, aligned {source, target} pairs come back, so the
  two view columns stay paragraph-aligned by construction.
- Long transcripts are batched by character budget to keep each call within
  Claude's output limit and avoid SSH timeouts.
- Any failure (SSH down, bad JSON, count mismatch) raises — the caller keeps
  the raw LibreTranslate result, so improvement is always non-destructive.
"""

import asyncio
import json
import logging
import re
import shlex
from typing import Dict, List

from app.config import settings

logger = logging.getLogger(__name__)


class LLMNotConfigured(Exception):
    """Raised when remote-Claude improvement is disabled or misconfigured."""


class LLMImproveError(Exception):
    """Raised when the remote Claude call fails or returns unusable output."""


class ClaudeRemoteService:
    PAIR_PROMPT = (
        "You are a professional subtitle/transcript editor and translator. "
        "The user message is JSON: {{\"segments\": [...]}} where each segment "
        "is a chunk of rough auto-transcribed text in {source_name}.\n\n"
        "Your job:\n"
        "1. Reflow the segments into logically coherent, well-punctuated "
        "paragraphs in {source_name} (fix capitalisation/punctuation, remove "
        "stutters and filler, but never invent content).\n"
        "2. For EACH resulting paragraph, also give a natural, fluent "
        "{target_name} translation that reads like a human wrote it.\n\n"
        "Return ONLY valid JSON, no markdown fences and no commentary, shaped "
        "exactly as: {{\"paragraphs\": [{{\"source\": \"...\", \"target\": "
        "\"...\"}}, ...]}}. Each paragraph object MUST have both keys. Keep "
        "source and target meaning identical and aligned one-to-one."
    )

    SUMMARY_PROMPT = (
        "Summarise the following text in {target_name} in 2-4 clear sentences. "
        "Return ONLY the summary text, no preamble, no markdown.\n\n{text}"
    )

    def __init__(self):
        self.enabled = settings.LLM_IMPROVE_ENABLED
        self.ssh_host = settings.CLAUDE_SSH_HOST
        self.ssh_user = settings.CLAUDE_SSH_USER
        self.ssh_key = settings.CLAUDE_SSH_KEY
        self.claude_bin = settings.CLAUDE_BIN
        self.model = settings.CLAUDE_MODEL
        self.timeout = settings.CLAUDE_TIMEOUT
        self.batch_chars = settings.CLAUDE_BATCH_CHARS

    def available(self) -> bool:
        return bool(self.enabled and self.ssh_host and self.ssh_user)

    # ---- public API -----------------------------------------------------

    async def improve(
        self,
        source_paragraphs: List[str],
        source_lang: str,
        target_lang: str,
    ) -> Dict:
        """Return {"paragraphs": [{"source", "target"}], "summary": str}."""
        if not self.available():
            raise LLMNotConfigured("Remote Claude improvement is not configured")

        segments = [p.strip() for p in source_paragraphs if p and p.strip()]
        if not segments:
            raise LLMImproveError("No text to improve")

        source_name = self._lang_name(source_lang)
        target_name = self._lang_name(target_lang)

        pairs: List[Dict[str, str]] = []
        for batch in self._batches(segments):
            pairs.extend(await self._improve_batch(batch, source_name, target_name))

        if not pairs:
            raise LLMImproveError("Claude returned no paragraphs")

        target_text = "\n\n".join(p["target"] for p in pairs)
        summary = await self._summarize(target_text, target_name)

        return {"paragraphs": pairs, "summary": summary}

    # ---- internals ------------------------------------------------------

    def _batches(self, segments: List[str]) -> List[List[str]]:
        batches: List[List[str]] = []
        current: List[str] = []
        size = 0
        for seg in segments:
            if current and size + len(seg) > self.batch_chars:
                batches.append(current)
                current, size = [], 0
            current.append(seg)
            size += len(seg)
        if current:
            batches.append(current)
        return batches

    async def _improve_batch(
        self, segments: List[str], source_name: str, target_name: str
    ) -> List[Dict[str, str]]:
        system = self.PAIR_PROMPT.format(
            source_name=source_name, target_name=target_name
        )
        payload = json.dumps({"segments": segments}, ensure_ascii=False)
        raw = await self._run_claude(f"{system}\n\n{payload}")
        data = self._parse_json_result(raw)

        paragraphs = data.get("paragraphs")
        if not isinstance(paragraphs, list) or not paragraphs:
            raise LLMImproveError("Claude response missing 'paragraphs' array")

        cleaned: List[Dict[str, str]] = []
        for item in paragraphs:
            if not isinstance(item, dict) or "source" not in item or "target" not in item:
                raise LLMImproveError("Claude paragraph missing 'source'/'target'")
            src = str(item["source"]).strip()
            tgt = str(item["target"]).strip()
            if src or tgt:
                cleaned.append({"source": src, "target": tgt})
        return cleaned

    async def _summarize(self, text: str, target_name: str) -> str:
        # Cap the input so the summary call stays small and fast.
        snippet = text[:8000]
        prompt = self.SUMMARY_PROMPT.format(target_name=target_name, text=snippet)
        try:
            raw = await self._run_claude(prompt)
            wrapper = json.loads(raw)
            return str(wrapper.get("result", "")).strip()
        except Exception as e:  # summary is best-effort; never fail the request
            logger.warning("Summary generation failed: %s", e)
            return ""

    async def _run_claude(self, prompt: str) -> str:
        """Run `claude -p` on the remote host, feeding the prompt via stdin.

        Returns the raw stdout, which is the `--output-format json` wrapper.
        """
        # Remote command is fully static (no transcript text) — the dynamic
        # prompt travels over stdin, so there is nothing to shell-escape here.
        remote_cmd = " ".join(
            shlex.quote(part)
            for part in [
                self.claude_bin,
                "-p",
                "--model",
                self.model,
                "--output-format",
                "json",
                "--max-turns",
                "1",
            ]
        )

        ssh_argv = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=10",
        ]
        if self.ssh_key:
            ssh_argv += ["-i", self.ssh_key]
        ssh_argv += [f"{self.ssh_user}@{self.ssh_host}", remote_cmd]

        logger.info("Invoking remote claude (%s, model=%s)", self.ssh_host, self.model)
        try:
            proc = await asyncio.create_subprocess_exec(
                *ssh_argv,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(prompt.encode()), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            raise LLMImproveError(f"Remote claude timed out after {self.timeout}s")
        except Exception as e:
            raise LLMImproveError(f"Failed to invoke remote claude: {e}")

        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()
            raise LLMImproveError(f"Remote claude exited {proc.returncode}: {err[:300]}")

        return stdout.decode(errors="replace")

    def _parse_json_result(self, raw: str) -> dict:
        """Unwrap the CLI envelope, strip code fences, parse the inner JSON."""
        try:
            wrapper = json.loads(raw)
        except json.JSONDecodeError:
            raise LLMImproveError("Remote claude returned non-JSON output")

        if wrapper.get("is_error"):
            raise LLMImproveError(
                f"Claude reported an error: {wrapper.get('result', '')[:200]}"
            )

        text = str(wrapper.get("result", "")).strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise LLMImproveError("Could not parse improved-translation JSON")

    @staticmethod
    def _lang_name(code: str) -> str:
        names = {
            "en": "English", "de": "German", "fr": "French", "es": "Spanish",
            "it": "Italian", "nl": "Dutch", "pt": "Portuguese", "ru": "Russian",
            "ja": "Japanese", "zh": "Chinese", "ko": "Korean", "ar": "Arabic",
            "tr": "Turkish", "pl": "Polish", "sv": "Swedish", "uk": "Ukrainian",
        }
        if not code or code == "auto":
            return "the original language"
        return names.get(code.lower().split("-")[0], code)
