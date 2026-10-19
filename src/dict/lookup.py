"""Dictionary lookup service using JMdict and KANJIDIC."""

from dataclasses import dataclass
from jamdict import Jamdict


@dataclass
class DictEntry:
    kanji: list[str]
    kana: list[str]
    meanings: list[str]
    pos: list[str]


class DictionaryEngine:
    def __init__(self):
        print("[DictionaryEngine] Initializing JMdict backend...")
        self.jam = Jamdict()

    def lookup_word(self, word: str, max_entries: int = 3) -> list[DictEntry]:
        """Lookup word in JMdict and return structured definitions."""
        if not word or not word.strip():
            return []

        result = self.jam.lookup(word.strip())
        entries: list[DictEntry] = []

        for entry in result.entries[:max_entries]:
            kanji_forms = [k.text for k in entry.kanji_forms]
            kana_forms = [k.text for k in entry.kana_forms]

            all_meanings = []
            all_pos = set()

            for sense in entry.senses:
                glosses = [g.text for g in sense.gloss]
                if glosses:
                    all_meanings.append("; ".join(glosses))
                for p in sense.pos:
                    all_pos.add(str(p))

            entries.append(
                DictEntry(
                    kanji=kanji_forms,
                    kana=kana_forms,
                    meanings=all_meanings,
                    pos=sorted(all_pos),
                )
            )

        return entries

    def lookup_kanji_details(self, char: str) -> dict | None:
        """Lookup single Kanji character details from KANJIDIC2."""
        if len(char) != 1:
            return None

        result = self.jam.lookup(char)
        if not result.chars:
            return None

        c = result.chars[0]
        return {
            "literal": c.literal,
            "stroke_count": c.stroke_count,
            "grade": c.grade,
            "meanings": c.meanings(lang="en"),
            "readings_on": [r.value for r in c.readings if r.type == "ja_on"],
            "readings_kun": [r.value for r in c.readings if r.type == "ja_kun"],
        }
