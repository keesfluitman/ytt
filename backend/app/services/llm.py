"""Improve machine translations with a remote Claude Code instance.

The container has no Anthropic API key. Instead it SSHes to a host where the
`claude` CLI is logged in (subscription OAuth) and runs it in headless/print
mode. The whole prompt is sent over stdin so no transcript text ever lands on
the remote shell command line (no escaping/injection surface); the remote
command itself is static.

Design notes:
- Claude reflows the transcript into logical paragraphs and returns the cleaned
  source and its translation together, so the two view columns are aligned by
  construction (no fragile paragraph-count matching).
- Output uses sentinel delimiters, not JSON: translated text routinely contains
  quotation marks, which corrupt model-generated JSON.
- Long transcripts are batched by character budget to keep each call within
  Claude's output limit and avoid SSH timeouts.
- assess() is a cheap pre-check that lets the caller skip already-good
  translations unless the user forces the improvement.
- Any failure (SSH down, unparseable output) raises — the caller keeps the raw
  LibreTranslate result, so improvement is always non-destructive.
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
    # Delimiter (not JSON) output: the translated text frequently contains
    # quotation marks, which break model-generated JSON. Sentinel lines can't be
    # broken by quotes, and letting Claude choose the paragraph count keeps the
    # source/target pairs aligned by construction (they come from one output).
    PARA_SEP = "===P==="
    TGT_SEP = "===T==="

    REFLOW_PROMPT = (
        "You are a professional subtitle editor and translator. The user message "
        "is JSON {{\"segments\": [...]}} of rough auto-transcribed {source_name} "
        "fragments.\n\n"
        "Reflow them into logically coherent, well-punctuated paragraphs in "
        "{source_name} (fix punctuation/capitalisation, remove stutters and "
        "filler, never invent content). For EACH resulting paragraph, also give a "
        "natural, fluent {target_name} translation.\n\n"
        "Output PLAIN TEXT only — no JSON, no numbering, no commentary. For each "
        "paragraph, output the cleaned {source_name}, then a line containing "
        "exactly ===T===, then the {target_name} translation. Separate paragraphs "
        "with a line containing exactly ===P==="
    )

    ASSESS_PROMPT = (
        "You are a translation quality reviewer. Below is a machine translation "
        "in {target_name}. Decide whether it already reads as natural, fluent "
        "{target_name}, or whether it reads as rough/literal machine output that "
        "would clearly benefit from rewriting.\n\n"
        "Reply with EXACTLY one line: either 'GOOD: <short reason>' or "
        "'IMPROVE: <short reason>'. Nothing else.\n\n"
        "Translation:\n{text}"
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

    async def assess(self, translation_text: str, target_lang: str) -> Dict:
        """Cheap pre-check: is the existing translation already good?

        Returns {"needs_improvement": bool, "reason": str}. Defaults to
        needs_improvement=True on any ambiguity (better to improve than to
        wrongly skip).
        """
        if not self.available():
            raise LLMNotConfigured("Remote Claude improvement is not configured")

        sample = (translation_text or "").strip()[:1800]
        if not sample:
            return {"needs_improvement": True, "reason": "no existing translation"}

        prompt = self.ASSESS_PROMPT.format(
            target_name=self._lang_name(target_lang), text=sample
        )
        text = self._result_text(await self._run_claude(prompt))
        line = (text.strip().splitlines() or [""])[0].strip()
        reason = line.split(":", 1)[1].strip() if ":" in line else line
        if line.upper().startswith("GOOD"):
            return {"needs_improvement": False, "reason": reason}
        return {"needs_improvement": True, "reason": reason}

    async def improve(
        self,
        source_paragraphs: List[str],
        source_lang: str,
        target_lang: str,
    ) -> Dict:
        """Reflow + translate the transcript into aligned source/target paragraphs.

        Returns {"segments": [...cleaned source...], "translations": [...],
        "summary": str}. Both lists come from the same model output, so they are
        aligned 1:1 by construction regardless of the raw paragraph count.
        Output uses sentinel delimiters (not JSON), so quotation marks in the
        text can't corrupt parsing.
        """
        if not self.available():
            raise LLMNotConfigured("Remote Claude improvement is not configured")

        segments = [p.strip() for p in source_paragraphs if p and p.strip()]
        if not segments:
            raise LLMImproveError("No text to improve")

        source_name = self._lang_name(source_lang)
        target_name = self._lang_name(target_lang)

        sources: List[str] = []
        translations: List[str] = []
        for batch in self._batches(segments):
            for src, tgt in await self._reflow_batch(batch, source_name, target_name):
                sources.append(src)
                translations.append(tgt)

        if not translations:
            raise LLMImproveError("Claude returned no paragraphs")

        summary = await self._summarize("\n\n".join(translations), target_name)

        return {"segments": sources, "translations": translations, "summary": summary}

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

    async def _reflow_batch(
        self, segments: List[str], source_name: str, target_name: str
    ) -> List[tuple]:
        """Return [(cleaned_source, translation), ...] for one batch."""
        system = self.REFLOW_PROMPT.format(
            source_name=source_name, target_name=target_name
        )
        payload = json.dumps({"segments": segments}, ensure_ascii=False)
        text = self._result_text(await self._run_claude(f"{system}\n\n{payload}"))

        pairs: List[tuple] = []
        for block in text.split(self.PARA_SEP):
            block = block.strip()
            if not block or self.TGT_SEP not in block:
                continue
            src, tgt = block.split(self.TGT_SEP, 1)
            src, tgt = src.strip(), tgt.strip()
            if src or tgt:
                pairs.append((src, tgt))

        if not pairs:
            raise LLMImproveError("Could not parse any paragraphs from Claude output")
        return pairs

    async def _summarize(self, text: str, target_name: str) -> str:
        # Cap the input so the summary call stays small and fast.
        snippet = text[:8000]
        prompt = self.SUMMARY_PROMPT.format(target_name=target_name, text=snippet)
        try:
            return self._result_text(await self._run_claude(prompt))
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

    def _result_text(self, raw: str) -> str:
        """Unwrap the CLI's --output-format json envelope (which is reliable,
        machine-generated JSON) and return the model's text, stripping any
        stray code fences. The model's text itself is NOT parsed as JSON."""
        try:
            wrapper = json.loads(raw)
        except json.JSONDecodeError:
            raise LLMImproveError("Remote claude returned a non-JSON envelope")

        if wrapper.get("is_error"):
            raise LLMImproveError(
                f"Claude reported an error: {wrapper.get('result', '')[:200]}"
            )

        text = str(wrapper.get("result", "")).strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()
        return text

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
