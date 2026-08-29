"""Deterministic exercise generation.

Every answer here is computed, never predicted. That is the whole point: a
model that marks a correct 9-year-old wrong does real damage, and the only
reliable way to prevent it is for the model never to be the one deciding.

Formats follow real Grundschule worksheets - see FORMATS.md.
"""

import random

from .models import Blank, Sheet, Task

MAX_TASKS = 8


def _rng(seed: int | None) -> random.Random:
    return random.Random(seed)


# -- plain arithmetic -------------------------------------------------------


def zr1000_add(rng: random.Random, count: int) -> list[Task]:
    tasks = []
    for i in range(count):
        a = rng.randint(120, 780)
        b = rng.randint(110, 999 - a) if a < 889 else rng.randint(1, 110)
        tasks.append(
            Task(
                id=str(i + 1),
                kind="arith",
                render=f"{a} + {b} =",
                blanks=[Blank(id="a", answer=str(a + b), label=f"{a} + {b}")],
                solution=[f"{a} + {b} = {a + b}"],
            )
        )
    return tasks


def zr1000_sub(rng: random.Random, count: int) -> list[Task]:
    tasks = []
    for i in range(count):
        a = rng.randint(300, 1000)
        b = rng.randint(100, a - 10)
        tasks.append(
            Task(
                id=str(i + 1),
                kind="arith",
                render=f"{a} - {b} =",
                blanks=[Blank(id="a", answer=str(a - b), label=f"{a} - {b}")],
                solution=[f"{a} - {b} = {a - b}"],
            )
        )
    return tasks


def zr1000_div(rng: random.Random, count: int, *, with_remainder: bool = True) -> list[Task]:
    """Division, in the German convention: `:` for divide, `R` for the remainder."""
    tasks = []
    for i in range(count):
        divisor = rng.randint(2, 9)
        quotient = rng.randint(11, 999 // divisor)
        remainder = rng.randint(1, divisor - 1) if (with_remainder and divisor > 1 and i % 2) else 0
        dividend = quotient * divisor + remainder

        if remainder:
            answer = f"{quotient} R {remainder}"
            steps = [
                f"{divisor} · {quotient} = {quotient * divisor}",
                f"{dividend} - {quotient * divisor} = {remainder}",
                f"Also {dividend} : {divisor} = {quotient} R {remainder}",
            ]
        else:
            answer = str(quotient)
            steps = [f"{divisor} · {quotient} = {dividend}", f"Also {dividend} : {divisor} = {quotient}"]

        tasks.append(
            Task(
                id=str(i + 1),
                kind="arith",
                render=f"{dividend} : {divisor} =",
                blanks=[Blank(id="a", answer=answer, label=f"{dividend} : {divisor}")],
                solution=steps,
                meta={"has_remainder": bool(remainder)},
            )
        )
    return tasks


def zr1000_mul(rng: random.Random, count: int) -> list[Task]:
    tasks = []
    for i in range(count):
        a = rng.choice([rng.randint(11, 99), rng.choice([20, 30, 40, 50, 60, 70, 80, 90])])
        b = rng.randint(2, 9)
        tasks.append(
            Task(
                id=str(i + 1),
                kind="arith",
                render=f"{a} · {b} =",
                blanks=[Blank(id="a", answer=str(a * b), label=f"{a} · {b}")],
                solution=[f"{a} · {b} = {a * b}"],
            )
        )
    return tasks


# -- pyramids ---------------------------------------------------------------

_LETTERS = "abcdefghij"


def _pyramid(rng: random.Random, index: int, *, multiply: bool, inverse: bool) -> Task:
    """A three-row pyramid. Adjacent cells combine into the cell above.

    Inverse pyramids give the apex and make the child work back down, which is
    exactly the case where a language model quietly gets it wrong.
    """
    op = "·" if multiply else "+"
    if multiply:
        base = [rng.randint(2, 10) for _ in range(3)]
    else:
        base = [rng.randint(4, 40) for _ in range(3)]

    combine = (lambda x, y: x * y) if multiply else (lambda x, y: x + y)
    mid = [combine(base[0], base[1]), combine(base[1], base[2])]
    top = combine(mid[0], mid[1])

    cells: dict[str, int] = {
        "u1": base[0], "u2": base[1], "u3": base[2],
        "m1": mid[0], "m2": mid[1],
        "t": top,
    }

    if inverse:
        # Give the apex, one middle and one base cell; blank the rest.
        given = {"t", "m1", "u1"}
    else:
        given = {"u1", "u2", "u3"}

    blank_keys = [k for k in ("t", "m1", "m2", "u1", "u2", "u3") if k not in given]
    letters = {key: _LETTERS[n] for n, key in enumerate(blank_keys)}

    def show(key: str) -> str:
        return str(cells[key]) if key in given else f"[{letters[key]}]"

    render = (
        f"        {show('t')}\n"
        f"     {show('m1')}   {show('m2')}\n"
        f"  {show('u1')}   {show('u2')}   {show('u3')}"
    )

    blanks = [
        Blank(id=letters[key], answer=str(cells[key]), label=_pyramid_label(key, cells, given, op))
        for key in blank_keys
    ]

    if inverse:
        inverse_op = ":" if multiply else "-"
        solution = [
            f"{cells['t']} {inverse_op} {cells['m1']} = {cells['m2']}",
            f"{cells['m1']} {inverse_op} {cells['u1']} = {cells['u2']}",
            f"{cells['m2']} {inverse_op} {cells['u2']} = {cells['u3']}",
        ]
    else:
        solution = [
            f"{base[0]} {op} {base[1]} = {mid[0]}",
            f"{base[1]} {op} {base[2]} = {mid[1]}",
            f"{mid[0]} {op} {mid[1]} = {top}",
        ]

    return Task(
        id=str(index + 1),
        kind="pyramid",
        render=render,
        blanks=blanks,
        solution=solution,
        meta={"multiply": multiply, "inverse": inverse},
    )


def _pyramid_label(key: str, cells: dict, given: set, op: str) -> str:
    parents = {"t": ("m1", "m2"), "m1": ("u1", "u2"), "m2": ("u2", "u3")}
    if key in parents:
        left, right = parents[key]
        return f"die Zahl über {left} {op} {right}"
    return "eine Zahl in der untersten Reihe"


def pyramids(rng: random.Random, count: int, *, multiply: bool) -> list[Task]:
    # Mix directions: the inverse ones are where the real learning is.
    return [
        _pyramid(rng, i, multiply=multiply, inverse=(i % 2 == 1))
        for i in range(count)
    ]


# -- operation grids --------------------------------------------------------


def grid(rng: random.Random, count: int, *, op: str) -> list[Task]:
    """Rechentabellen: an operator, column headers, row headers, blank cells."""
    tasks = []
    for i in range(count):
        if op == "·":
            cols = rng.sample([2, 3, 4, 5, 8, 10], 3)
            rows = rng.sample([12, 20, 30, 40, 50, 60], 2)
            apply = lambda r, c: r * c  # noqa: E731
        elif op == ":":
            cols = rng.sample([2, 4, 5, 8, 10], 3)
            rows = [c * rng.randint(11, 60) for c in cols[:2]] + [rng.choice(cols) * 40]
            rows = rows[:2]
            apply = lambda r, c: r // c  # noqa: E731
        else:
            cols = rng.sample([8, 65, 130, 180, 260], 3)
            rows = rng.sample([330, 640, 710, 860], 2)
            apply = lambda r, c: r - c  # noqa: E731

        if op == ":":
            # Only keep cells that divide exactly - a grid full of remainders is noise.
            cols = [c for c in cols if all(r % c == 0 for r in rows)] or [1]

        header = "  " + "  ".join(f"{c:>5}" for c in cols)
        lines = [f"{op:>4} |{header}"]
        blanks: list[Blank] = []
        n = 0
        for r in rows:
            cells = []
            for c in cols:
                letter = _LETTERS[n]
                n += 1
                cells.append(f"{'[' + letter + ']':>7}")
                blanks.append(
                    Blank(id=letter, answer=str(apply(r, c)), label=f"{r} {op} {c}")
                )
            lines.append(f"{r:>4} |" + "".join(cells))

        tasks.append(
            Task(
                id=str(i + 1),
                kind="grid",
                render="\n".join(lines),
                blanks=blanks,
                solution=[f"{b.label} = {b.answer}" for b in blanks],
                meta={"op": op},
            )
        )
    return tasks


# -- topic registry ---------------------------------------------------------

TOPIC_SHEETS: dict[str, dict] = {
    "plus_minus": {
        "title": "Rechnen im Zahlenraum 1000",
        "instruction": "Löse die Aufgaben.",
        "build": lambda rng, n: zr1000_add(rng, n // 2) + _renumber(zr1000_sub(rng, n - n // 2), n // 2),
    },
    "mal_geteilt": {
        "title": "Multiplizieren und Dividieren",
        "instruction": "Löse die Aufgaben. Schreibe den Rest als R.",
        "build": lambda rng, n: zr1000_mul(rng, n // 2) + _renumber(zr1000_div(rng, n - n // 2), n // 2),
    },
    "schriftlich": {
        "title": "Dividieren mit und ohne Rest",
        "instruction": "Löse die Aufgaben. Schreibe den Rest als R.",
        "build": lambda rng, n: zr1000_div(rng, n),
    },
    "zahlenmauern": {
        "title": "Malpyramiden",
        "instruction": "Multipliziere in den Malpyramiden. Fülle die Felder in eckigen Klammern.",
        "build": lambda rng, n: pyramids(rng, min(n, 4), multiply=True),
    },
    "rechentabellen": {
        "title": "Rechentabellen",
        "instruction": "Fülle die Tabellen aus.",
        "build": lambda rng, n: grid(rng, min(n, 3), op="·"),
    },
    "einmaleins": {
        "title": "Das kleine Einmaleins",
        "instruction": "Löse die Aufgaben.",
        "build": lambda rng, n: zr1000_mul(rng, n),
    },
}


def _renumber(tasks: list[Task], offset: int) -> list[Task]:
    for n, task in enumerate(tasks):
        task.id = str(offset + n + 1)
    return tasks


def build_sheet(topic_id: str, *, count: int = 6, seed: int | None = None) -> Sheet:
    spec = TOPIC_SHEETS.get(topic_id)
    if spec is None:
        raise KeyError(f"no generator for topic {topic_id!r}")
    count = max(1, min(count, MAX_TASKS))
    return Sheet(
        topic_id=topic_id,
        title=spec["title"],
        instruction=spec["instruction"],
        tasks=spec["build"](_rng(seed), count),
    )


def generatable_topics() -> list[str]:
    return sorted(TOPIC_SHEETS)
