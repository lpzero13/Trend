# Working in Trend / Tori Market Lab

- Canonical repository: `https://github.com/lpzero13/Trend`. Application code is in `alpaca-trendlinien/`, not the repository root.
- Read `HERMES.md` for goals, current scope, operational constraints and the roadmap. Keep its implemented/planned distinction accurate when changing behavior.
- Preserve the manual web chart and headless research interfaces. Chart and research must share causal source-interval calculations. MTF drawing projections are not entry signals.
- Research defaults are experiment assumptions, not validated trading rules. Do not introduce broker orders or claim portfolio profitability from fixed-horizon observations.
- Never commit credentials, runtime data, databases, market datasets, user snapshots, logs, local artifacts or virtual environments. Leave personal browser drawings separate from automatic research.
- Runtime Python dependencies belong in `alpaca-trendlinien/requirements.txt`. No Node runtime/build is required by the application. Preserve bundled library licensing and attribution.
- Run relevant tests from `alpaca-trendlinien/`: `python -m unittest discover -s tests -q`; JS checks: `node --test tests/test_geometry.cjs tests/test_snapshot_view.cjs tests/test_measurements.cjs`. Unit tests must not require real provider credentials.
- The service uses `/var/lib/tori`; direct CLI tools must use the same `TORI_DATA_DIR`. Do not silently change a production database path, resume old jobs under different engine code, or overwrite local secrets during an update.
- Prefer `codex/` branches for future feature work. Initial repository bootstrap follows the repository's configured `main` default. Preserve remote work and never force-push to replace it.
- A user request or authorized task must cover publishing changes. This repository association alone is not an instruction to deploy containers, send notifications or execute trades.
