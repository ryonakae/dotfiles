import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import unicodedata
from itertools import pairwise

BLOCK_START = re.compile(r"^(?:[-*+] |\d+[.)] |#{1,6}(?: |$)|> |```|~~~|\|)")
FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
SENTENCE_END = re.compile(r"[。！？.!?][\"'”’」』）】)}\]]*$")


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


def indentation(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def fence_marker(line: str) -> str | None:
    match = FENCE_LINE.match(line)
    if not match:
        return None

    marker, rest = match.groups()
    if marker[0] == "`" and "`" in rest:
        return None
    return marker


def closes_fence(line: str, active_fence: str) -> bool:
    match = FENCE_LINE.match(line)
    if not match:
        return False

    marker, rest = match.groups()
    return (
        marker[0] == active_fence[0]
        and len(marker) >= len(active_fence)
        and not rest.strip()
    )


def ends_hard_line_break(line: str) -> bool:
    return line.endswith("\\") or len(line) - len(line.rstrip(" ")) >= 2


def ends_sentence(line: str) -> bool:
    return bool(SENTENCE_END.search(line.rstrip()))


def reaches_wrap_boundary(line: str, content_width: int | None) -> bool:
    if content_width is None:
        return False
    return display_width(line) >= max(1, content_width - 1)


def contains_shifted_fence(lines: list[str]) -> bool:
    for line in lines:
        stripped = line.lstrip(" ")
        if len(line) - len(stripped) > 3 and fence_marker(stripped) is not None:
            return True
    return False


def infer_partial_margin(lines: list[str], pane_width: int | None) -> int:
    if indentation(lines[0]) != 0:
        return 0

    following = [line for line in lines[1:] if line]
    if not following:
        return 0

    margin = min(len(line) - len(line.lstrip(" ")) for line in following)
    if margin == 0:
        return 0

    if any(
        fence_marker(line) is not None or fence_marker(line[margin:]) is not None
        for line in lines
    ):
        return 0

    if margin == 1:
        return margin

    if (
        isinstance(pane_width, bool)
        or not isinstance(pane_width, int)
        or pane_width <= margin + 1
    ):
        return 0

    content_width = pane_width - margin - 1
    stripped_following = [line[margin:] for line in following]
    sentence_index = next(
        (index for index, line in enumerate(stripped_following) if ends_sentence(line)),
        None,
    )
    if sentence_index is None:
        return 0

    has_wrapped_line_before_sentence = any(
        reaches_wrap_boundary(line, content_width)
        for line in stripped_following[:sentence_index]
    )
    return margin if has_wrapped_line_before_sentence else 0


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
    lines = ["" if not line.strip() else line for line in normalized.split("\n")]

    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        return ""

    indents = [indentation(line) for line in lines if line]
    partial_margin = infer_partial_margin(lines, pane_width)
    partial_first_line = partial_margin > 0
    if partial_first_line:
        common_indent = partial_margin
        lines = [
            line if index == 0 or not line else line[partial_margin:]
            for index, line in enumerate(lines)
        ]
    else:
        common_indent = min(indents, default=0)
        lines = textwrap.dedent("\n".join(lines)).split("\n")

    content_width = None
    if pane_width is not None and pane_width > 0 and not contains_shifted_fence(lines):
        content_width = max(1, pane_width - common_indent - 1)

    output = [lines[0]]
    active_fence = fence_marker(lines[0])
    for index, (current, following) in enumerate(pairwise(lines)):
        reaches_boundary = reaches_wrap_boundary(current, content_width) or (
            partial_first_line
            and content_width is not None
            and index == 0
            and not ends_sentence(current)
        )
        preserve_newline = (
            not current
            or not following
            or active_fence is not None
            or starts_block(following)
            or fence_marker(following) is not None
            or fence_marker(current) is not None
            or ends_hard_line_break(current)
            or not reaches_boundary
        )
        if preserve_newline:
            output.append("\n")
        else:
            output.append(join_separator(current, following, content_width))
        output.append(following)

        if active_fence is None:
            active_fence = fence_marker(following)
        elif closes_fence(following, active_fence):
            active_fence = None

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
        width = pane["rect"]["width"]
        if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
            return None
        return width
    except (
        OSError,
        subprocess.SubprocessError,
        KeyError,
        TypeError,
        ValueError,
        StopIteration,
        json.JSONDecodeError,
    ):
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

    clipboard = subprocess.run(
        ["pbpaste"], check=True, capture_output=True
    ).stdout.decode("utf-8")
    transformed = normalize(clipboard, pane_width)
    subprocess.run(["pbcopy"], check=True, input=transformed.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
