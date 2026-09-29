#!/usr/bin/env python3
"""Deterministic text corpus for the `textview` bench app.

Generates the same ~1 MiB / 5,000-paragraph corpus on every invocation
(fixed LCG seed, fixed word list): one paragraph per line, lowercase
ASCII words only (no markup-significant characters), so the text can be
embedded verbatim in Lumen markup attributes.

Outputs:
  * harness/out/corpus.txt           - read at startup by the five native
                                       textview apps (path via $BENCH_CORPUS)
  * harness/out/lumen-apps/textview/src/main.lmn
                                     - the Lumen textview app markup, with
                                       the same 5,000 paragraphs inlined as
                                       <label wrap="word"> elements into the
                                       empty doc-col of the copy bench.py
                                       takes from the Lumen repo (Lumen's
                                       Rhai API has no file I/O, so the
                                       corpus ships inside the markup; see
                                       results.md caveats). Skipped when
                                       there is no copy.

Both are build artifacts: `bench.py build` regenerates them.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_TXT = ROOT / "harness" / "out" / "corpus.txt"
LUMEN_TEXTVIEW_LMN = (ROOT / "harness" / "out" / "lumen-apps" / "textview"
                      / "src" / "main.lmn")

PARAGRAPHS = 5000

# 64 fixed words; strictly [a-z] so no escaping is ever needed (Lumen
# text attributes treat {, }, &, <, >, " specially).
WORDS = (
    "the quick brown fox jumps over a lazy dog while morning light "
    "spills across quiet rooftops and distant hills where rivers bend "
    "through valleys carrying stories from mountain springs toward open "
    "sea past villages markets towers gardens bridges orchards fields "
    "lanterns windows doorways cellars attics stairwells corridors "
    "harbors islands forests meadows glaciers deserts canyons plateaus "
    "written spoken remembered forgotten beneath beyond within between "
    "against"
).split()
assert len(WORDS) == 64, len(WORDS)

MASK = (1 << 64) - 1
MUL = 6364136223846793005
INC = 1442695040888963407


def generate():
    """Return the 5,000 paragraphs (list of str). Deterministic."""
    state = 0x42
    paragraphs = []

    def nxt(n):
        nonlocal state
        state = (state * MUL + INC) & MASK
        return (state >> 33) % n

    for _ in range(PARAGRAPHS):
        n_words = 20 + nxt(25)  # 20..44 words
        ws = [WORDS[nxt(64)] for _ in range(n_words)]
        ws[0] = ws[0].capitalize()
        paragraphs.append(" ".join(ws) + ".")
    return paragraphs


# The line in the Lumen textview shell the paragraphs go after.
DOC_COL = '<column class="doc-col">'


def write_outputs():
    paragraphs = generate()
    text = "\n".join(paragraphs) + "\n"
    CORPUS_TXT.parent.mkdir(parents=True, exist_ok=True)
    CORPUS_TXT.write_text(text)

    if LUMEN_TEXTVIEW_LMN.is_file():
        shell = LUMEN_TEXTVIEW_LMN.read_text()
        head, sep, tail = shell.partition(DOC_COL + "\n")
        if not sep:
            raise SystemExit(f"{LUMEN_TEXTVIEW_LMN}: no {DOC_COL} line")
        labels = "".join(
            f'      <label class="para" wrap="word" text="{p}" />\n'
            for p in paragraphs)
        LUMEN_TEXTVIEW_LMN.write_text(head + sep + labels + tail)
    return len(text)


if __name__ == "__main__":
    n = write_outputs()
    print(f"corpus: {PARAGRAPHS} paragraphs, {n} bytes -> {CORPUS_TXT}")
    if LUMEN_TEXTVIEW_LMN.is_file():
        print(f"lumen textview markup -> {LUMEN_TEXTVIEW_LMN}")
