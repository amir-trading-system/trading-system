# FRVP indicator validation requirement

For any change touching `frvp_new_indicator.pine`, its detection behavior, its
plots used for CSV export, `test_frvp_reclaim_regression.py`, or the frozen FRVP
fixtures:

1. Keep Pine and Python detection logic synchronized.
2. Increment `VALIDATION_BUILD_ID` in both Pine and Python for every Pine
   detection-logic change.
3. Run `python3 scripts/verify_frvp_release.py --record` from the repository
   root after the full regression passes.
4. Never describe the release as fully verified unless
   `python3 scripts/verify_frvp_release.py --require-pine-traces` passes against
   current-build TradingView CSV exports.
5. Report the Python fixture counts and Pine-runtime parity count separately.

Do not bypass or weaken the attestation gate to make a change appear valid.
