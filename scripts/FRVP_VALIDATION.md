# FRVP validation gate

The indicator has two separate validation levels. They must never be reported
as though they are the same thing.

## 1. Source-locked Python regression

Run:

```bash
python3 scripts/verify_frvp_release.py
```

This verifies that:

- the Pine source, Python mirror, validation gate, and all frozen CSV fixtures
  exactly match the most recently attested release;
- Pine and Python expose the same named parity-rule regions;
- both files use the same `VALIDATION_BUILD_ID`;
- all curated positive, negative, setup, timing, and line-price tests pass.

Any edit to the Pine source invalidates the attestation. After a deliberate
detection change, update the Python mirror, increment `VALIDATION_BUILD_ID`,
run the complete suite, and record the new result:

```bash
python3 scripts/verify_frvp_release.py --record
```

The gate refuses to record a detection change when the Python detection region
did not also change, or when the build ID was not incremented.

## 2. Actual TradingView Pine-runtime parity

Python cannot execute Pine Script locally. Full verification therefore uses
TradingView itself as the Pine runtime:

1. Add the current indicator to a one-minute TradingView chart with its default
   detection settings.
2. Export chart data for each regression symbol/date with indicator values.
3. Save each export in `scripts/fixtures/frvp_pine_traces/` using the same file
   name as its frozen fixture in `scripts/fixtures/frvp/`.
4. Run:

```bash
python3 scripts/verify_frvp_release.py --require-pine-traces
```

The export must contain `Validation Build ID`, `Strong Reclaim Entry`, and
`Nested Reclaim Evidence Marker`. The gate rejects an older build and compares
every Pine entry/setup timestamp with Python—not just the known positive bars.

Only a release showing `FULLY_VERIFIED` has passed actual Pine-runtime parity.
`PYTHON_VERIFIED_PINE_RUNTIME_PENDING` means the Python suite passed but fresh
TradingView exports are still missing.

## Frozen fixtures

Regression inputs live in `scripts/fixtures/frvp/`; tests no longer depend on
mutable files in Downloads. To deliberately rebuild a fixture from a reviewed
source export, update and run:

```bash
python3 scripts/freeze_frvp_validation_fixtures.py
```

Changing any frozen fixture invalidates the release attestation.
