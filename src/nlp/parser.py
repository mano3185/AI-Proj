"""Morphological tokenizer and de-inflector using SudachiPy."""

from dataclasses import dataclass, field
from sudachipy import tokenizer, dictionary


@dataclass
class Token:
    surface: str
    dictionary_form: str
    reading: str
    part_of_speech: tuple[str, ...]
    is_content_word: bool
    definitions: list[dict] = field(default_factory=list)

    @property
    def pos_category(self) -> str:
        return self.part_of_speech[0] if self.part_of_speech else "未知語"


class JapaneseParser:
    def __init__(self, mode: str = "C"):
        """Initialize SudachiPy tokenizer.
        Modes:
          - 'A': Shortest units (e.g., '選挙' + '管理' + '委員会')
          - 'B': Middle units
          - 'C': Compound words (e.g., '選挙管理委員会') - default for dictionary lookups
        """
        dict_obj = dictionary.Dictionary()
        self.tokenizer = dict_obj.create()
        split_modes = {
            "A": tokenizer.Tokenizer.SplitMode.A,
            "B": tokenizer.Tokenizer.SplitMode.B,
            "C": tokenizer.Tokenizer.SplitMode.C,
        }
        self.split_mode = split_modes.get(mode.upper(), tokenizer.Tokenizer.SplitMode.C)

    def parse(self, text: str) -> list[Token]:
        """Parse Japanese text into tokens with dictionary forms."""
        if not text:
            return []

        morphemes = self.tokenizer.tokenize(text, self.split_mode)
        tokens = []

        # Content word POS tags (Nouns, Verbs, Adjectives, Adverbs)
        content_pos = {"名詞", "動詞", "形容詞", "形状詞", "副詞"}

        for m in morphemes:
            pos = m.part_of_speech()
            surface = m.surface()
            dict_form = m.dictionary_form()
            reading = m.reading_form()

            is_content = pos[0] in content_pos if pos else False

            tokens.append(
                Token(
                    surface=surface,
                    dictionary_form=dict_form,
                    reading=reading,
                    part_of_speech=pos,
                    is_content_word=is_content,
                )
            )

        return tokens
