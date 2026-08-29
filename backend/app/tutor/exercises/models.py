from dataclasses import dataclass, field


@dataclass
class Blank:
    """One thing the child has to fill in."""

    id: str          # "a", "b" ... unique within the task
    answer: str      # canonical form, always produced by Python
    label: str = ""  # what it is, for hints ("die Spitze", "560 : 8")


@dataclass
class Task:
    id: str            # "1", "2" ... unique within the sheet
    kind: str          # "arith" | "pyramid" | "grid"
    render: str        # what the child sees
    blanks: list[Blank]
    solution: list[str] = field(default_factory=list)  # worked steps, hint level 3
    meta: dict = field(default_factory=dict)

    @property
    def single(self) -> bool:
        return len(self.blanks) == 1


@dataclass
class Sheet:
    topic_id: str
    title: str
    instruction: str
    tasks: list[Task]
