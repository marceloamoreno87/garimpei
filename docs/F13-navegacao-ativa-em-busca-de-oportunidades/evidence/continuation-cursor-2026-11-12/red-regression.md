# Regression before correction

Command: `uv run --project apps/backend --frozen --no-sync pytest -c apps/backend/pyproject.toml apps/backend/tests/unit/test_navigation_continuation.py -q`.

Observed before implementation: **1 failed,5 passed**, exit1. The cross-adapter native-cursor test asserted `first_page.continuation == "source:" + cursor`; actual was numeric `"2"`. The synthetic cursor reproduced the length/character-class limitations observed independently in the real-source diagnostic, without retaining a real cursor.

The failure demonstrated loss of the native continuation at the public source boundary. The correction was then applied;14 unit cases and3 PostgreSQL cases passed. Initial lint/type annotations in new test/migration files were fixed before the final six-gate pass. These initial failures were not counted as successful validation.
