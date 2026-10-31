#!/usr/bin/env python3
"""Registry and checker of the Spec Kit identifiers (see specs/_global/CONVENTIONS.md).

Every identifier is written ``<NNN>-<KIND>`` where NNN is the number of the feature (``specs/NNN-*``), e.g.
``001-FR-029``, ``003-US2``, ``003-US2-4`` (scenario 4 of story 2), ``002-SC-005``, ``004-T017``, ``003-D7``,
``001-I14``, ``002-Q1``. A bare ``FR-029`` is never accepted: the same number exists in several features.

    python utils/spec_ids.py check             # definitions unique, citations resolve, no bare identifier
    python utils/spec_ids.py show 001-FR-029   # the definition and everything that cites it
    python utils/spec_ids.py refs 001-FR-029   # where it is cited
    python utils/spec_ids.py registry          # rewrite specs/_global/registry.md
    python utils/spec_ids.py next 004 T        # next free number of a kind in a feature

Standard library only; run from anywhere inside the repository.
"""
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
REGISTRY = SPECS / "_global" / "registry.md"

KIND = r"(?:US\d+(?:-\d+)?|FR-\d+[a-z]?|SC-\d+|T\d{3,}|D\d+|I\d+|Q\d+)"
QUALIFIED = re.compile(r"(?<![\w-])(?P<spec>\d{3})-(?P<kind>" + KIND + r")(?![\w])")
# Identifiers without the feature number. D, I, Q only count after the word that introduces them.
SCENARIO = re.compile(r"^(US\d+)-\d+$")
BARE = re.compile(
    r"(?<![A-Za-z0-9./-])(?:US\d+(?:-\d+)?|FR-\d+[a-z]?|SC-\d+|T\d{3})(?![\w-]*\w)"
    r"|(?<![\w-])(?:research(?:\.md)?|decisions?|clarifications?|findings?)\s+(?:§\s*)?[DRIQ]\d+(?![\w])",
    re.I,
)
# Places that describe the format with placeholders or examples, or are not project text.
EXEMPT = (
    ".specify/templates/",
    ".claude/skills/",
    ".specify/extensions/",
    ".specify/workflows/",
    ".specify/scripts/",
    "specs/_global/CONVENTIONS.md",
    "utils/spec_ids.py",
    "utils/docs_screenshots/",
)
TEXT_SUFFIXES = {".py", ".md", ".html", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".json", ".po", ".sh", ".rst"}


def files():
    out = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split("\n")
    for name in out:
        path = ROOT / name
        if name and path.suffix in TEXT_SUFFIXES and path.is_file() and name != "specs/_global/registry.md":
            yield name, path


def spec_of(name):
    m = re.match(r"specs/(\d{3})-", name)
    return m.group(1) if m else None


def definitions():
    """{qualified id: (file, line number, text)} and a list of definition problems."""
    found, problems = {}, []

    def add(qid, name, number, text):
        if qid in found:
            problems.append(f"{name}:{number}: {qid} is also defined at {found[qid][0]}:{found[qid][1]}")
        found[qid] = (name, number, text.strip())

    for name, path in files():
        spec = spec_of(name)
        if not spec or "/" in name[len(f"specs/{spec}-"):].split("/", 1)[0]:
            continue
        base = name.split("/", 2)[2] if name.count("/") >= 2 else ""
        questions = 0
        for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            for m in re.finditer(r"^\s*(?:[-*]\s*)?\*\*(\d{3}-(?:FR|SC)-\d+[a-z]?)\*\*", line):
                add(m.group(1), name, number, line)
            m = re.match(r"^#{2,4}\s+User Story (\d+)\b", line)
            if m:
                add(f"{spec}-US{m.group(1)}", name, number, line)
            m = re.match(r"^\s*-\s*\[.\]\s*(\d{3}-T\d{3,})\b", line)
            if m:
                add(m.group(1), name, number, line)
            m = re.match(r"^#{2,4}\s+(\d{3}-D\d+)\b", line)
            if m:
                add(m.group(1), name, number, line)
            m = re.match(r"^\s*[-*]\s*\*\*(\d{3}-I\d+)\b", line)
            if m:
                add(m.group(1), name, number, line)
            m = re.match(r"^\s*Retired:", line)
            if m:  # an identifier that is gone for good is never reused: "Retired: 001-SC-001 (reason)"
                for r in QUALIFIED.finditer(line):
                    add(f"{r.group('spec')}-{r.group('kind')}", name, number, line)
            if base == "spec.md" and re.match(r"^\s*-\s*Q:", line):
                questions += 1
                add(f"{spec}-Q{questions}", name, number, line)
    for qid, (name, number, _) in found.items():
        if not name.startswith(f"specs/{qid[:3]}-"):
            problems.append(f"{name}:{number}: {qid} is defined in the folder of feature {spec_of(name)}")
    return found, problems


def citations():
    """{qualified id: [(file, line)]}, scenario suffixes (US1-3) are reduced to the story."""
    refs = defaultdict(list)
    for name, path in files():
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            for m in QUALIFIED.finditer(line):
                kind = SCENARIO.sub(r"\1", m.group("kind"))
                refs[f"{m.group('spec')}-{kind}"].append((name, number))
    return refs


def bare_identifiers():
    bad = []
    for name, path in files():
        if name.startswith(EXEMPT):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            for m in BARE.finditer(line):
                bad.append((name, number, m.group(0)))
    return bad


def check():
    found, problems = definitions()
    refs = citations()
    for qid, places in sorted(refs.items()):
        if qid not in found:
            for name, number in places:
                if not name.startswith(EXEMPT):
                    problems.append(f"{name}:{number}: {qid} is not defined in specs/{qid[:3]}-*")
    for name, number, text in bare_identifiers():
        problems.append(f"{name}:{number}: '{text}' has no feature number (write e.g. 001-{text.split()[-1]})")
    for problem in problems:
        print(problem)
    print(f"{len(found)} identifiers defined, {sum(len(v) for v in refs.values())} citations, {len(problems)} problems")
    return 1 if problems else 0


def normalise(qid):
    m = re.fullmatch(r"(\d{3})-(" + KIND + ")", qid)
    if not m:
        sys.exit(f"{qid!r} is not a qualified identifier (NNN-KIND, e.g. 001-FR-029)")
    return m.group(1) + "-" + SCENARIO.sub(r"\1", m.group(2))


def show(qid, only_refs=False):
    qid = normalise(qid)
    found, _ = definitions()
    refs = citations().get(qid, [])
    if not only_refs:
        if qid not in found:
            print(f"{qid}: not defined")
        else:
            name, number, text = found[qid]
            print(f"{qid} defined at {name}:{number}\n  {text}")
    print(f"cited {len(refs)} times" + (":" if refs else ""))
    for name, number in refs:
        print(f"  {name}:{number}")


def next_free(spec, kind):
    found, _ = definitions()
    kind = kind.upper()
    numbers = [
        int(re.search(r"(\d+)[a-z]?$", q).group(1)) for q in found if q.startswith(spec + "-") and re.match(
            rf"{spec}-{re.escape(kind)}-?\d", q)
    ]
    n = max(numbers, default=0) + 1
    print(f"{spec}-{kind}{'-' if kind in ('FR', 'SC') else ''}{n:0{3 if kind in ('FR', 'SC', 'T') else 1}d}")


def title(text):
    text = re.sub(r"^\s*(?:[-*]\s*)?(?:\[.\]\s*)?", "", text)
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"\*\*\d{3}-[A-Z]+-?\d+[a-z]?\*\*:?\s*", "", text)
    text = text.replace("|", "\\|")
    return text if len(text) <= 110 else text[:107].rstrip() + "..."


def registry():
    found, _ = definitions()
    refs = citations()
    lines = [
        "# Identifier registry",
        "",
        "Generated by `python utils/spec_ids.py registry` - do not edit. Convention: [CONVENTIONS.md](CONVENTIONS.md).",
        "`Cited` counts the citations outside the feature's own `specs/` folder (code, tests, docs, changelog).",
        "",
    ]
    for spec in sorted({q[:3] for q in found}):
        folder = next(p.name for p in SPECS.iterdir() if p.name.startswith(spec + "-"))
        lines += [f"## {folder}", "", "| ID | Definition | Cited |", "|---|---|---|"]

        def order(q):
            return re.sub(r"[\d-]+[a-z]?$", "", q[4:]), int(re.search(r"(\d+)", q[4:]).group(1)), q

        ids = [q for q in found if q.startswith(spec + "-") and not re.match(rf"{spec}-T\d", q)]
        for qid in sorted(ids, key=order):
            name, number, text = found[qid]
            outside = sum(1 for n, _ in refs.get(qid, []) if not n.startswith(f"specs/{spec}-"))
            lines.append(f"| `{qid}` | [{title(text)}](../{name[6:]}#L{number}) | {outside or ''} |")
        tasks = sum(1 for q in found if q.startswith(f"{spec}-T"))
        lines += ["", f"{tasks} tasks (`{spec}-T001`...) in [tasks.md](../{folder}/tasks.md).", ""]
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REGISTRY.relative_to(ROOT)}")


def main(argv):
    if argv[:1] == ["check"]:
        return check()
    if argv[:1] == ["show"] and len(argv) == 2:
        return show(argv[1])
    if argv[:1] == ["refs"] and len(argv) == 2:
        return show(argv[1], only_refs=True)
    if argv[:1] == ["registry"]:
        return registry()
    if argv[:1] == ["next"] and len(argv) == 3:
        return next_free(argv[1], argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
