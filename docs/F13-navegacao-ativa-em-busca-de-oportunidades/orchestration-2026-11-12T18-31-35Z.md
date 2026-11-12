# Orchestration — F13 continuity recovery

Started: 2026-11-12T18-31-35Z
Branch: fix/F13-prova-continuidade
Scope: resume implemented F13; inspect real-source continuation read-only, correct reproducible defects, preserve prior evaluation and histories. User authorized parallel agents and master integration; branch commits authorized, no push.
Budget: up to three correction cycles; no external messages.

## Initial state

Base 3ce35d5, clean worktree. F13 implemented, cycles=2, 19 PASS/1 MANUAL in eval-report-2026-11-12T17-57-33Z.md. E2E-PERCURSO-01 lacked a confirmed exact next-cursor unit. Primary profile is not opened or copied; initial diagnosis uses SELECTs only.

## Execution

- Read current canonical spec, plan, contract and previous real-source summary.
- Acquired exclusive process-owned lock under .runtime/f13-continuity/feature.lock.

### Correction cycle 1 — Native cursor preservation

- Primary SELECT baseline: 1,015 receipts, 164 successful first-page receipts and 164 continuation_scope_mismatch failures. No successful exact cursor continuation was established.
- Diagnostic operational failures were not evidence: first lifecycle attempt stopped the DB before DI and made zero source searches (OperationalError); normal init restored all readiness checks. A subsequent preflight found no product-kind interests and stopped before lifecycle/browser. The corrected helper selected a configured query with a valid URL before stopping.
- One exclusive, read-only source search returned 20 cards and an opaque cursor of 1,674 characters, rejected both by the 480-character cap and the assumed base64 alphabet. No raw cursor, geographic inputs, profile or cookies were exported. Normal stop/init preserved state; final readiness HTTP200, all four checks ready.
- Regression RED: cross-adapter test expected the native opaque cursor but received numeric "2".
- Fix: shared bounded printable-ASCII validation (4,096 chars), byte-for-byte parser value, JSON-only cursor transport, additive schema4103 including source: prefix. Numeric legacy checkpoints retain the existing one-step rebuild with historical receipts and page budget preserved.
- GREEN: 14 focused unit cases; 3 PostgreSQL cases (4,096-character persistence and hashed identity, cycle rebuild admission, numeric legacy clearing without receipt loss). Six Python gates, Django check, drift and build exit0.
- Preliminary patch committed as167135fbd45ca8b5b2a7c3975154577e7c812bce; coordinator integrated master85427ab and restarted the primary normally.
- Full suite started on frozen patch inputs (467 tracked inputs hashed), while read-only exact-unit correlation runs against the primary for at most300seconds.

### Final-suite scheduling adjustment

The first single-process run was interrupted gracefully at coordinator direction for latency, after66PASS in949.11seconds; exit2/KeyboardInterrupt is preserved in full-suite-interrupted.txt and is not counted as final approval. An owned synthetic F16 lab remained alive after interrupted fixture setup; checkout/disposable/session_kind/process ownership were verified and stop.sh --clean returned0. Its already-removed private temp configuration was recovered only in memory from the verified owned process, without publishing values. No principal data/profile was touched.

The final full collection512 is now partitioned into305/207 disjoint cases using the previous validated504-run file partition. Both shard commands must exit0, JUnit identifiers must equal the frozen collection with multiplicity1, and all467 input hashes must remain identical. The interrupted run is independent historical evidence.

### Correction cycle 2 — Complete F07 evaluation precondition

Final shard0 passed305 cases in1114.91seconds, exit0. Shard1 finished206PASS/1FAIL in898.16seconds, exit1. The single failure was F07 test_integrated_composition_matrix_and_cost_edits: synthetic target709 was still awaiting its evaluation. A separate unchanged reproduction failed identically in12seconds.

Diagnosis: profit_scenario checked for zero NULL current_id among existing progress rows, ignoring listings whose progress row had not yet been created by batched reconciliation. It could claim all valuations ready before the next batch. The coordinator authorized a stronger precondition using LEFT JOIN from listings, with every financial assertion preserved.

Only apps/backend/tests/integration/test_profit.py changed. Its fixture has exactly four consumers, all in shard1; no external importer or consumer was found. Source-segment comparison proved all four test bodies byte-identical. RED→GREEN: the unchanged financial scenario passed in17.78seconds after the wait correction. Six gates passed again. Commitd6e8b4bd4d3ee279b04be4477c7544182413ed2c integrated by coordinator in master780fead and forwarded to the other teams.

The original failed shard1 log/JUnit/exit1 remain under failed-shard-1-before-fixture.*. The entire207-case shard1 is reexecuting in the corrected source; the305-case shard0 remains applicable because its consumers and production code are unchanged. Final manifest must record this distinction and must not count the failed trial as PASS. No assertion, financial rule, retry timeout or gate was relaxed.

## Final result

**Status:** success
**Finished:**2026-11-12T19:32:55.995403+00:00
**Final evaluation:**[eval-report-2026-11-12T19-32-55Z.md](eval-report-2026-11-12T19-32-55Z.md) — clean,20PASS/0FAIL/0BLOCKED/0MANUAL/0SKIPPED; all7ACs verified.
**Complete regression:**512PASS, JUnit identifiers each exactly once in final validation, exit0/0;305-case shard unchanged production source and207-case shard corrected fixture. All467 final inputs stable; only intentional fixture difference between shard sources.
**Cycles:**2 in this resumed run (native cursor and F07 precondition),4 cumulative.
**Cleanup:** no owned eval processes alive. Primary retained normally; application browser proof session closed; process-owned lock released at commit finalization.
