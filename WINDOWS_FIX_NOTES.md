# STREAM-SURE v1.0.1 — Windows SQLite lifecycle fix

## Problem observed

On Windows/Python 3.12, three tests failed during temporary-directory cleanup with:

`PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`

The affected files were temporary SQLite databases (`api.db`, `x.db`). The certification logic itself completed correctly; the failure occurred after the assertions when `TemporaryDirectory` attempted to delete a database file that still had an open SQLite connection.

A second issue was found in `scripts/validate.ps1`: PowerShell's `$ErrorActionPreference = "Stop"` does not automatically convert a non-zero exit code from native programs such as `python.exe` into a terminating error. Therefore the script continued to the benchmark and printed a misleading success message even when `unittest` returned a failure exit code.

## Fixes in v1.0.1

1. Added deterministic `SQLiteStore.close()` lifecycle management.
2. Added idempotent `StreamSureService.close()` and context-manager support.
3. API test teardown now stops the server, joins the server thread, closes the service/database, then removes the temporary directory.
4. SQLite-based core tests now use `with StreamSureService(...)` so database handles are released before temporary-directory cleanup.
5. API server now closes the persistent database in a `finally` block during normal/KeyboardInterrupt shutdown.
6. `validate.ps1` now checks `$LASTEXITCODE` after every Python command and throws on non-zero exit status.

## Validation after patch

- Automated tests: **19/19 passed**
- Test result: **OK**
- Environment doctor: passed
- Smoke benchmark: completed

The fix changes resource lifecycle and validation correctness only; it does not change the STREAM-SURE decision semantics or frozen E1–E16/B0–B5 research design.
