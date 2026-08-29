"""Topic tree for the German Grundschule, classes 2-4.

Phase 1 uses this to steer the tutor and to label sessions; phase 2 hangs the
exercise generators off the same topic ids.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    id: str
    subject: str  # "math" | "german"
    de: str
    en: str
    classes: tuple[int, ...]


TOPICS: list[Topic] = [
    # --- Mathematik ---
    Topic("zahlenraum_100", "math", "Zahlenraum bis 100", "Numbers up to 100", (2,)),
    Topic("zahlenraum_1000", "math", "Zahlenraum bis 1000", "Numbers up to 1000", (3,)),
    Topic("zahlenraum_million", "math", "Zahlenraum bis 1 Million", "Numbers up to 1 million", (4,)),
    Topic("plus_minus", "math", "Plus und Minus mit Übertrag", "Adding and subtracting with carrying", (2, 3, 4)),
    Topic("einmaleins", "math", "Das kleine Einmaleins", "Times tables", (2, 3)),
    Topic("mal_geteilt", "math", "Mal und Geteilt", "Multiplying and dividing", (3, 4)),
    Topic("schriftlich", "math", "Schriftliche Rechenverfahren", "Written arithmetic", (3, 4)),
    Topic("groessen_geld", "math", "Geld", "Money", (2, 3, 4)),
    Topic("groessen_zeit", "math", "Uhrzeit und Zeitspannen", "Telling the time", (2, 3, 4)),
    Topic("groessen_laenge", "math", "Längen und Gewichte", "Lengths and weights", (3, 4)),
    Topic("geometrie", "math", "Formen und Symmetrie", "Shapes and symmetry", (2, 3, 4)),
    Topic("sachaufgaben", "math", "Sachaufgaben", "Word problems", (2, 3, 4)),
    # --- Deutsch ---
    Topic("rechtschreibung", "german", "Rechtschreibung", "Spelling", (2, 3, 4)),
    Topic("gross_klein", "german", "Groß- und Kleinschreibung", "Capitalisation", (2, 3, 4)),
    Topic("wortarten", "german", "Wortarten", "Word classes", (3, 4)),
    Topic("satzzeichen", "german", "Satzarten und Satzzeichen", "Sentence types and punctuation", (3, 4)),
    Topic("silben", "german", "Silben und Silbentrennung", "Syllables", (2, 3)),
    Topic("wortschatz", "german", "Wortschatz", "Vocabulary", (2, 3, 4)),
    Topic("lesen", "german", "Lesen und Verstehen", "Reading comprehension", (2, 3, 4)),
]

BY_ID = {topic.id: topic for topic in TOPICS}


def for_class(school_class: int, subject: str | None = None) -> list[Topic]:
    return [
        topic
        for topic in TOPICS
        if school_class in topic.classes and (subject is None or topic.subject == subject)
    ]


def label(topic: Topic, language: str) -> str:
    return topic.de if language == "de" else topic.en
