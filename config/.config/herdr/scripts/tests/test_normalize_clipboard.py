import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "normalize-clipboard.py"


class NormalizeClipboardTest(unittest.TestCase):
    def normalize(
        self,
        text: str,
        pane_width: int | None = None,
        env: dict[str, str] | None = None,
    ) -> str:
        command = [sys.executable, SCRIPT, "--filter"]
        if pane_width is not None:
            command.extend(["--pane-width", str(pane_width)])

        result = subprocess.run(
            command,
            input=text,
            capture_output=True,
            check=True,
            env=env,
            text=True,
        )
        return result.stdout

    def test_preserves_logical_line_breaks_between_wrapped_messages(self) -> None:
        copied = """ 原因はかなり明確です。現実装は「空行・Markdown ブロック開始以外の単一改行を
 原則すべて連結」しており、ペイン幅は連結可否ではなく空白挿入の判定にしか使
 っていません。さらに fenced code block 内の改行も潰れます。
 安全側に直すには、幅から折り返しと判断できる改行だけを連結し、判断不能な改
 行・コードブロックは保持する方針がよさそうです。実際に崩れたコピー元と、期
 待する整形後テキストの例を1件だけ貼ってもらえますか？その例を回帰テストにし
 ます。
 原因は特定できました。具体例を1件もらえれば、改行を保守的に扱う判定へ変更し
 、回帰テスト付きで改善できます。"""
        expected = """原因はかなり明確です。現実装は「空行・Markdown ブロック開始以外の単一改行を原則すべて連結」しており、ペイン幅は連結可否ではなく空白挿入の判定にしか使っていません。さらに fenced code block 内の改行も潰れます。
安全側に直すには、幅から折り返しと判断できる改行だけを連結し、判断不能な改行・コードブロックは保持する方針がよさそうです。実際に崩れたコピー元と、期待する整形後テキストの例を1件だけ貼ってもらえますか？その例を回帰テストにします。
原因は特定できました。具体例を1件もらえれば、改行を保守的に扱う判定へ変更し、回帰テスト付きで改善できます。"""

        self.assertEqual(self.normalize(copied, pane_width=77), expected)

    def test_normalizes_copy_started_midway_through_wrapped_line(self) -> None:
        copied = """最初の折り返しだけは正しく判定できない可能
 性があります。

 判定は「現在行がペイン幅近くまであるか」なので、途中から選択すると先頭行が
 短くなり、本来の表示折り返しを論理改行として保持してしまいます。2行目以降の
 折り返しは通常どおり判定できます。"""
        expected = """最初の折り返しだけは正しく判定できない可能性があります。

判定は「現在行がペイン幅近くまであるか」なので、途中から選択すると先頭行が短くなり、本来の表示折り返しを論理改行として保持してしまいます。2行目以降の折り返しは通常どおり判定できます。"""

        self.assertEqual(self.normalize(copied, pane_width=77), expected)

    def test_infers_wider_agent_margins_from_wrapped_prose(self) -> None:
        cases = [(2, "wrapped sentence"), (4, "wrapped wordsx")]

        for margin, continuation in cases:
            with self.subTest(margin=margin):
                copied = f"fragment\n{' ' * margin}{continuation}\n{' ' * margin}done."
                expected = f"fragment {continuation} done."
                self.assertEqual(self.normalize(copied, pane_width=20), expected)

    def test_does_not_infer_wider_margin_from_indented_single_line(self) -> None:
        cases = [
            "fragment\n  short",
            "heading\n  This is intentionally indented and long enough to wrap.",
        ]

        for copied in cases:
            with self.subTest(copied=copied):
                self.assertEqual(self.normalize(copied, pane_width=20), copied)

    def test_does_not_infer_margin_around_fenced_code(self) -> None:
        copied = """fragment
    ```
    123456789012345
    ```"""

        self.assertEqual(self.normalize(copied, pane_width=20), copied)

    def test_preserves_sentence_break_after_partial_first_line(self) -> None:
        copied = """短い文です。
 次の論理行です。"""
        expected = """短い文です。
次の論理行です。"""

        self.assertEqual(self.normalize(copied, pane_width=77), expected)

    def test_partial_first_line_stays_separate_without_pane_width(self) -> None:
        copied = "fragment\n continuation"
        expected = "fragment\ncontinuation"
        env = os.environ.copy()
        env.pop("HERDR_ACTIVE_PANE_ID", None)
        env.pop("HERDR_BIN_PATH", None)

        self.assertEqual(self.normalize(copied, env=env), expected)

    def test_preserves_mixed_indentation(self) -> None:
        copied = " \talpha\n  beta"
        expected = "\talpha\n beta"

        self.assertEqual(self.normalize(copied, pane_width=77), expected)

    def test_trims_surrounding_whitespace_only_lines(self) -> None:
        self.assertEqual(self.normalize(" \ntext\n ", pane_width=77), "text")

    def test_preserves_line_breaks_inside_fenced_code_blocks(self) -> None:
        copied = """```
print("12345678901234567890")
print("next")
```"""

        self.assertEqual(self.normalize(copied, pane_width=24), copied)

    def test_fenced_code_does_not_trigger_partial_line_inference(self) -> None:
        copied = """```python
 print("x")
 ```"""

        self.assertEqual(self.normalize(copied, pane_width=77), copied)

    def test_preserves_indented_fenced_code_blocks(self) -> None:
        copied = """intro
   ````
abcdefghij
next
   ````
outro"""

        self.assertEqual(self.normalize(copied, pane_width=11), copied)

    def test_shorter_fence_does_not_close_code_block(self) -> None:
        copied = """````
abcdefghij
```
abcdefghij
next
````"""

        self.assertEqual(self.normalize(copied, pane_width=11), copied)

    def test_preserves_markdown_hard_line_breaks(self) -> None:
        cases = ["abcdefgh  \nnext", "abcdefghi\\\nnext"]

        for copied in cases:
            with self.subTest(copied=copied):
                self.assertEqual(self.normalize(copied, pane_width=12), copied)

    def test_invalid_active_pane_width_preserves_ambiguous_newlines(self) -> None:
        copied = "abcdefghij\nnext"

        for width in (None, 0, -1, True, 1.5, float("inf")):
            with self.subTest(width=width), tempfile.TemporaryDirectory() as directory:
                fake_herdr = Path(directory) / "herdr"
                response = {
                    "result": {
                        "layout": {
                            "panes": [
                                {
                                    "pane_id": "pane-1",
                                    "rect": {"width": width},
                                }
                            ]
                        }
                    }
                }
                fake_herdr.write_text(
                    f"#!/bin/sh\nprintf '%s\\n' '{json.dumps(response)}'\n"
                )
                fake_herdr.chmod(0o755)
                env = os.environ | {
                    "HERDR_ACTIVE_PANE_ID": "pane-1",
                    "HERDR_BIN_PATH": str(fake_herdr),
                }

                self.assertEqual(self.normalize(copied, env=env), copied)

    def test_active_pane_lookup_failure_preserves_ambiguous_newlines(self) -> None:
        copied = "abcdefghij\nnext"
        scripts = ["exit 1", "printf 'not-json\\n'"]

        for script in scripts:
            with (
                self.subTest(script=script),
                tempfile.TemporaryDirectory() as directory,
            ):
                fake_herdr = Path(directory) / "herdr"
                fake_herdr.write_text(f"#!/bin/sh\n{script}\n")
                fake_herdr.chmod(0o755)
                env = os.environ | {
                    "HERDR_ACTIVE_PANE_ID": "pane-1",
                    "HERDR_BIN_PATH": str(fake_herdr),
                }

                self.assertEqual(self.normalize(copied, env=env), copied)


if __name__ == "__main__":
    unittest.main()
