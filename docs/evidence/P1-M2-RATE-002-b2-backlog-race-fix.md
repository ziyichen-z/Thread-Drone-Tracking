# P1-M2-RATE-002 — B2 release transport-race fix

Date: 2026-07-27

Status: `STABLE_CANDIDATE_AWAITING_SONNET`

Candidate: `433d816` (`1dd7d30..433d816`)

## Live failure retained

The first corrected-scene B2 smoke initialized the reviewed NanoTrack-v2
identity from frozen frame 97 and reached a healthy moving heartbeat. The
coordinator embedded ready frame 177 in release command
`rate2-release-1785206625148809000`, but Unity rejected the command as
`backlog_out_of_range` and remained in `HOLD`. At the final pause both
`frames/latest.json` and tracker-ready had advanced to frame 496
(`seq=400`); evaluator time/frame count remained `0/0`. No ack, accepted
command, release provenance, summary, qualification, status or formal attempt
was produced.

After Play exited, the session, rejected command/state/receipt, 497 retained
frame pairs, 400 HOLD records, zero-time metrics, incomplete run and Editor
log were moved without deletion to:

`runtime/test-results/ut-p1-m2-rate-002-002-b2-smoke/attempt1-backlog-race/`

Key SHA-256:

- command: `29e0eb6c19188e9fcb9396604bf92f44435bc574a79dfd10cf7ade2a4e716a70`
- state: `9680ee0775608c35226c86787d951d991a383f533bf00cd390091f15ada5c421`
- rejection: `838905d2b4ca670430395bd551c184231f2663b44e163001cb37ec2bbf583a3c`
- final ready: `caee8f1e19a4eccd63066b6402a777b8e4bc1bacad87d59e45da7dd68645c0bb`
- evaluator metrics: `5a29882532e0b871d6bc6690cb61e700808cb795cd368ae40acedc358b4d191a`
- run manifest / records:
  `e4f7501b619ce38f820636848a3b9eab649afb11c31480a7a838901e0a30d8c6` /
  `e4c038cc7b9e0c35df4879a1b7b22bdd518770a41f5a012bec73d0c4dc4bf2a8`
- Editor log: `67cefb23449646f46e3a5df57b8fdfe6732319d436fb2bb32a2df68567c73a7d`

The active B2 campaign and user-confirmed calibration remain unchanged
(`4beb0571…33a` / `6ad25a07…b6a`). All active session/exchange/frame/
`rs2-pilot` slots are absent; qualification remains unconsumed.

## Root cause

`coordinate_release()` accepted a locally valid ready record with backlog
either 0 or 1 and used a 50 ms poll interval. At 20 Hz, accepting backlog 1
already spent the only frame allowed by the Unity transaction. If the atomic
file command arrived just after Unity's current Update, the next authoritative
check could observe backlog 2. The helper also did not reread
`frames/latest.json` after reading ready, so publication could advance inside
that read-to-write interval.

Unity behaved correctly: it retained the accepted invariant
`0 <= current_frame_id - last_processed_frame_id <= 1`, persisted the
rejection and stayed in `HOLD`. The fix therefore belongs solely to the
coordinator and must not relax Unity's gate.

## Candidate behavior

`tools/run_rate2_study.py` now:

1. still requires two advancing, fresh, identity-valid heartbeat reads;
2. skips an otherwise valid ready record when its observed backlog is 1;
3. rereads the latest-frame pointer and publishes only when both reads equal
   `ready.last_processed_frame_id`, reserving one frame for command transport;
4. uses a 5 ms default release poll (one tenth of a 20 Hz frame) and exposes
   `--poll-interval-s` for an auditable invocation;
5. leaves Unity ack validation, the accepted `[0,1]` range, schemas, state
   transitions and failure behavior unchanged.

`tests/test_rate2_protocol.py` now recreates the failure shape
deterministically: the first advancing ready is one frame behind and must be
skipped; the next ready catches up; simulated transport consumes one frame;
the resulting ack reports accepted backlog 1 and the provenance chain is
archived. The pre-fix coordinator would send the first record and fail this
ack.

## Implementer verification

- Focused regression:
  `.venv-track/bin/python -m unittest
  tests.test_rate2_protocol.Rate2ProtocolTests.test_coordinator_reserves_transport_frame_then_archives_ack
  -v` → 1/1 PASS.
- Full Python suite:
  `.venv-track/bin/python -m unittest discover -s tests -v` → 76/76 PASS.
- `.venv-track/bin/python -m py_compile controller/*.py tools/*.py tests/*.py`
  → PASS.
- `.venv-track/bin/python -m pip check` → no broken requirements.
- `git diff --check` → PASS.

No C#, Unity state-machine, tracker, evaluator, metric, scenario, model or
truth-boundary file changed. A Unity rerun is intentionally not authorized
until independent review passes.

## Sonnet review scope

Review the real diff `1dd7d30..433d816`, specifically:

1. whether requiring coordinator-side zero backlog plus a second latest read
   is a valid stricter implementation of the accepted `[0,1]` transaction;
2. whether the sequence-advance and heartbeat freshness requirements remain
   intact for skipped backlog-1 records;
3. whether 5 ms polling and the CLI override introduce any busy-wait,
   timeout, provenance or compatibility risk;
4. whether the regression would fail the old implementation and correctly
   models one frame of command transport;
5. whether Unity remains the only authoritative state owner and no identity,
   metric or truth boundary changed.

Required verdict goes in `docs/reviews/P1-M2-RATE-002.md`. Only `PASS` or
non-blocking `PASS_WITH_NOTES` authorizes rebuilding the smoke-only
`rs2-pilot` session and rerunning B2 attempt 2. The shared formal 30 s pilot
remains blocked until that smoke passes.
