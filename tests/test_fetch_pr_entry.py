from __future__ import annotations

import base64
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from fetch_pr_entry import (  # noqa: E402
    MAX_FILE_BYTES,
    PullRequestEntryError,
    REQUIRED_ENTRY_PATHS,
    _decode_contents_base64,
    head_coordinates,
    materialize_entry,
    module_ref_from_event,
)


HEAD_SHA = "a" * 40


def event(base_ref: str = "tool/docker", head_sha: str = HEAD_SHA) -> dict:
    return {
        "pull_request": {
            "base": {"ref": base_ref},
            "head": {
                "sha": head_sha,
                "repo": {"full_name": "example/OpenDevIndex"},
            },
        }
    }


class FetchPullRequestEntryTests(unittest.TestCase):
    def test_module_ref_comes_from_target_branch_not_head_branch(self) -> None:
        self.assertEqual(module_ref_from_event(event("tool/docker")), "tool/docker")

    def test_core_branch_cannot_be_used_as_module_target(self) -> None:
        with self.assertRaisesRegex(PullRequestEntryError, "module pull request must target"):
            module_ref_from_event(event("main"))
        with self.assertRaisesRegex(PullRequestEntryError, "unsupported module category"):
            module_ref_from_event(event("fix/docker"))

    def test_head_sha_must_be_full_hex(self) -> None:
        with self.assertRaisesRegex(PullRequestEntryError, "40-character"):
            head_coordinates(event(head_sha="main"))

    def test_contents_api_wrapped_base64_is_accepted(self) -> None:
        raw = b"GitHub wraps Contents API base64 across lines."
        encoded = base64.b64encode(raw).decode("ascii")
        wrapped = "\n".join(encoded[index : index + 12] for index in range(0, len(encoded), 12))
        self.assertEqual(_decode_contents_base64(wrapped, "entry/README.md"), raw)

    def test_invalid_base64_is_still_rejected(self) -> None:
        with self.assertRaisesRegex(PullRequestEntryError, "invalid base64"):
            _decode_contents_base64("not-base64!!!", "entry/README.md")

    def test_materializes_only_required_entry_text_files(self) -> None:
        seen: list[str] = []

        def fake_fetch(repository: str, sha: str, path: str, token: str | None) -> bytes:
            self.assertEqual(repository, "example/OpenDevIndex")
            self.assertEqual(sha, HEAD_SHA)
            self.assertEqual(token, "read-token")
            seen.append(path)
            return f"content for {path}\n".encode()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            module_ref, sha = materialize_entry(
                event(), root, fetcher=fake_fetch, token="read-token"
            )
            self.assertEqual(module_ref, "tool/docker")
            self.assertEqual(sha, HEAD_SHA)
            self.assertEqual(tuple(seen), REQUIRED_ENTRY_PATHS)
            for relative in REQUIRED_ENTRY_PATHS:
                self.assertTrue((root / relative).is_file())
            self.assertEqual(
                sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()),
                sorted(REQUIRED_ENTRY_PATHS),
            )

    def test_rejects_oversized_entry_file(self) -> None:
        def oversized(*_args: object) -> bytes:
            return b"x" * (MAX_FILE_BYTES + 1)

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(PullRequestEntryError, "validation limit"):
                materialize_entry(event(), Path(temp), fetcher=oversized)

    def test_rejects_non_utf8_entry_file(self) -> None:
        def non_utf8(*_args: object) -> bytes:
            return b"\xff\xfe"

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(PullRequestEntryError, "UTF-8"):
                materialize_entry(event(), Path(temp), fetcher=non_utf8)

    def test_rejects_nul_bytes(self) -> None:
        def nul_data(*_args: object) -> bytes:
            return b"hello\x00world"

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(PullRequestEntryError, "NUL"):
                materialize_entry(event(), Path(temp), fetcher=nul_data)


if __name__ == "__main__":
    unittest.main()
