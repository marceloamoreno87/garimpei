# Cursor length and hash conventions

The independent source diagnostic measured Feed.cursor before the internal source: prefix:1,674 native characters. Its sha256 also covers that native value only.

The exact-unit observation read the persisted checkpoint cursor. Its cursor_length and cursor_sha256 cover the entire stored string including the seven-character source: prefix. Thus the successful input was2,078 stored characters /2,071 native characters, and the next stored continuation was2,410 /2,403 native. The mapper derives the page unit hash from the stored value, so the correlation used the correct exact input.

The untouched original JSON evidence files retain their original measurements. No raw cursor, native value or private payload is included.

Public text/XML log copies have trailing display whitespace normalized for Git diff checks; the original private .runtime outputs remain unchanged. JUnit identifiers, verdicts, counts and timestamps are preserved.
