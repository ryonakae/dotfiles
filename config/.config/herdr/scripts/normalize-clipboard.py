import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import unicodedata
from itertools import pairwise

BLOCK_START = re.compile(
    r"^(?:[-*+] |\d+[.)] |#{1,6}(?: |$)|> |```|~~~|\|)"
)


def display_width(text: str) -> int:
    width = 0
    for char in text:
        if char == "\t":
            width += 4
        elif unicodedata.combining(char) or unicodedata.category(char) == "Cf":
            continue
        elif unicodedata.east_asian_width(char) in {"W", "F"}:
            width += 2
        else:
            width += 1
    return width


def starts_block(line: str) -> bool:
    return bool(BLOCK_START.match(line))


def join_separator(current: str, following: str, content_width: int | None) -> str:
    if content_width is not None and display_width(current) >= content_width:
        return ""

    if not current or not following:
        return ""

    if current[-1].isspace() or following[0].isspace():
        return ""

    current_is_ascii_word = current[-1].isascii() and current[-1].isalnum()
    following_is_ascii_word = following[0].isascii() and following[0].isalnum()
    if current_is_ascii_word and following_is_ascii_word:
        return " "

    return ""


def normalize(text: str, pane_width: int | None = None) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    dedented = textwrap.dedent(normalized)
    lines = dedented.split("\n")

    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        return ""

    common_indent = min(
        (len(line) - len(line.lstrip(" \t")) for line in normalized.split("\n") if line.strip()),
        default=0,
    )
    content_width = None
    if pane_width is not None:
        content_width = max(1, pane_width - common_indent - 1)

    output = [lines[0]]
    for current, following in pairwise(lines):
        preserve_newline = (
            not current
            or not following
            or starts_block(following)
            or current.startswith(("```", "~~~"))
        )
        if preserve_newline:
            output.append("\n")
        else:
            output.append(join_separator(current, following, content_width))
        output.append(following)

    return "".join(output)


def active_pane_width() -> int | None:
    pane_id = os.environ.get("HERDR_ACTIVE_PANE_ID")
    herdr = os.environ.get("HERDR_BIN_PATH")
    if not pane_id or not herdr:
        return None

    try:
        result = subprocess.run(
            [herdr, "pane", "layout", "--pane", pane_id],
            check=True,
            capture_output=True,
            text=True,
        )
        layout = json.loads(result.stdout)["result"]["layout"]
        pane = next(pane for pane in layout["panes"] if pane["pane_id"] == pane_id)
        return int(pane["rect"]["width"])
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, StopIteration, json.JSONDecodeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", action="store_true")
    parser.add_argument("--pane-width", type=int)
    args = parser.parse_args()

    pane_width = args.pane_width if args.pane_width is not None else active_pane_width()

    if args.filter:
        sys.stdout.write(normalize(sys.stdin.read(), pane_width))
        return 0

    clipboard = subprocess.run(["pbpaste"], check=True, capture_output=True).stdout.decode("utf-8")
    transformed = normalize(clipboard, pane_width)
    subprocess.run(["pbcopy"], check=True, input=transformed.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
