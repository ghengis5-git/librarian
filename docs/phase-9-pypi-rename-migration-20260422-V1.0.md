# Phase 9 — PyPI Distribution Rename Migration

**Date:** 2026-04-22
**Version:** 1.0
**Status:** Planning — NOT STARTED. Gated behind v0.8.0 ship.
**Author:** Christopher A. Kahn
**Scope:** Evaluate whether to rename the PyPI distribution from `librarian-2026` to `librarian` (or a different clean name), and define the mechanics for doing so without breaking existing installs.

---

## Why this is a separate phase

The `librarian-2026` dist name was chosen in Phase F V1.1 (2026-04-13) as a **temporary fallback** after the team discovered that `librarian` on PyPI was already occupied. That decision was never revisited. This phase revisits it.

This work is **explicitly out of scope for v0.8.0**. Session 53's pre-release work (Pass 4 findings, YAML errors, Windows/UNC hardening) is orthogonal. v0.8.0 ships as `librarian-2026` on PyPI. Any dist-name migration is a separate release cycle — most likely v0.9.0 or v1.0.0 depending on which path is chosen.

---

## Ground truth as of 2026-04-22

### PyPI `librarian` — occupied

| Field | Value |
|-------|-------|
| Owner | Nekroze (Taylor Lawson) |
| Owner email | nekroze@eturnilnetwork.com |
| Homepage | https://github.com/Nekroze/librarian |
| Description | "Python advanced card game library" |
| Latest release | 0.3.0 on 2013-09-01 (12.6 years ago) |
| Development status | Alpha |
| Yanked? | No |
| Total releases | 2 (0.2.7, 0.3.0) |

Verified live: `https://pypi.org/pypi/librarian/json` returned HTTP 200 with this metadata on 2026-04-22.

### Alternate names confirmed available (PyPI 404)

- `librarian-governance` — available
- `doc-librarian` — available
- `docs-librarian` — available
- `librariand` — available

### PEP 541 abandonment criteria (need ALL met)

Source: `https://peps.python.org/pep-0541/`.

| Criterion | Status for `librarian` |
|-----------|-------------------------|
| Owner not reachable (3+ contact attempts over 6 weeks) | Not yet attempted — required prerequisite |
| No releases in past 12 months | ✓ (12+ years) |
| No activity from owner on home page | ✓ — the linked GitHub repo is likewise dormant, to be confirmed on request |

Meets "abandoned" bar. But that alone is not sufficient — see Path A below.

---

## Three paths — decision matrix

| Dimension | A: PEP 541 → take `librarian` | B: Pick new clean name | C: Stay on `librarian-2026` |
|-----------|-------------------------------|------------------------|------------------------------|
| End dist name | `pip install librarian` | `pip install librarian-governance` (or similar) | `pip install librarian-2026` |
| PyPI-owner contact required | Yes — 3 attempts over 6 weeks, document in writing | No | No |
| PyPI workgroup request required | Yes — open issue on `pypi/support`, defend "notability" and "why can't you use a different name" | No | No |
| Probability of success | ~50/50. PEP 541 is routinely rejected when a working alternative name exists, and `librarian-2026` already works. The workgroup will ask the exact question that makes Path B attractive. | 100% | 100% |
| Timeline | 6-12 weeks minimum (PyPI response windows are slow) | 1-2 hours (upload new dist) | 0 |
| Marketing / brand cost | Cleanest final name | Clean enough — avoids the 2026 date stamp looking stale in 2027+ | Name literally contains a year; looks dated by 2027 |
| Backward compatibility work | Wrapper package on `librarian-2026` to redirect installs. Identical to Path B. | Wrapper package on `librarian-2026` to redirect installs | None needed |
| Risk of breakage for existing users | Low (wrapper shim) | Low (wrapper shim) | Zero |
| Cost if it fails | Wasted 6-12 weeks; fall back to B or C | N/A | N/A |

### My recommendation

**Path B — pick `librarian-governance` (or similar) now; ship as v0.9.0.** Rationale:

- The `librarian-2026` date-stamped name will look stale fast. v0.9.0 is a good moment to migrate before external adoption grows.
- Path A has a non-trivial rejection risk driven precisely by Path B's existence. The PyPI workgroup will ask: "Why do you need the bare `librarian` name when `librarian-governance` is available, descriptive, and available right now?" That question has no good answer for a solo project with zero external users yet.
- Path A is not cheap — documented contact attempts, 6-week reachability windows, a written case for notability, and a clean fallback if rejected. Net expected value is negative once you price the calendar time.
- Path B gives 90% of the branding benefit (no date stamp) at 1% of the cost.
- If the user ever *does* want the bare `librarian` name later, Path A can still be pursued from a position of strength (an established, adopted `librarian-governance` package with downloads, issues, stars — all of which actually help a PEP 541 notability argument).

**Path C is viable** if the user doesn't care about the date-stamp aesthetic and just wants to stop spending cycles on naming. Also reasonable.

**Path A is viable** only if the user wants the bare name enough to eat the timeline and the rejection risk. Not the default.

Decision is the user's. This plan covers all three.

---

## Path B detail — the recommended path

### Name candidates (rank-ordered)

1. **`librarian-governance`** — most descriptive; ties into the existing "document governance" tagline; available. Cons: longer to type.
2. **`doc-librarian`** — clean, short, available. Cons: "doc" is slightly ambiguous (could read as Python docstring tool).
3. **`docs-librarian`** — same as above, slightly less ambiguous. Available.
4. **`librariand`** — compact daemon-style name. Cons: suggests a long-running service, which this is not.

Working recommendation: **`librarian-governance`**.

### Backward-compat mechanic — stub wrapper on `librarian-2026`

`librarian-2026` does not disappear. It becomes a **deprecation wrapper** that transitively installs the new name.

**Wrapper `pyproject.toml`** (held in a `packaging/librarian-2026-wrapper/` subdirectory of the main repo, or in a throwaway branch):

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "librarian-2026"
version = "0.9.0"
description = "DEPRECATED — renamed to librarian-governance. This package is a compatibility shim."
requires-python = ">=3.10"
dependencies = [
    "librarian-governance==0.9.0",
]

[project.urls]
Homepage = "https://github.com/ghengis5-git/librarian"
```

No source code. No entry points. Just a metadata package that pulls in the real thing.

**Wrapper `librarian_2026/__init__.py`** (if we include a token module at all — optional, just for the DeprecationWarning):

```python
"""Compatibility shim — librarian-2026 has been renamed to librarian-governance."""
import warnings

warnings.warn(
    "librarian-2026 is deprecated. Use 'pip install librarian-governance' instead. "
    "This shim will continue to work until 2027-04-22, after which installs should "
    "target librarian-governance directly.",
    DeprecationWarning,
    stacklevel=2,
)
```

This is cosmetic — most users will never import `librarian_2026`, they'll import `librarian` (the Python module name, which stays unchanged). The DeprecationWarning path fires only if someone does `import librarian_2026`, which no existing user does today. So the real deprecation signal is:

- The wrapper's PyPI description literally says "DEPRECATED"
- `pip install librarian-2026` prints a dependency-resolution line showing it resolves to `librarian-governance`

That is enough for a solo project with a handful of users.

### Release choreography

Assume current state is post-v0.8.0 ship on `librarian-2026` (v0.8.0 already published as `librarian-2026==0.8.0`).

**Step 1 — publish `librarian-governance==0.9.0`**
- Rename `name = "librarian-2026"` → `name = "librarian-governance"` in `pyproject.toml`.
- Bump `version = "0.8.0"` → `version = "0.9.0"`.
- Bump `librarian/__init__.py`: `__version__ = "0.9.0"`.
- Run full test suite.
- `python -m build` → produces `librarian_governance-0.9.0-py3-none-any.whl` + `librarian_governance-0.9.0.tar.gz`.
- `twine upload dist/librarian_governance-0.9.0*`.
- Smoke test: fresh venv, `pip install librarian-governance`, `python -c "import librarian; print(librarian.__version__)"` → `0.9.0`.

**Step 2 — publish `librarian-2026==0.9.0` wrapper**
- Separate build. Clean `dist/`.
- Use the wrapper `pyproject.toml` from above. Same version number `0.9.0` so `pip install librarian-2026` gives the same underlying functionality as `pip install librarian-governance`.
- `python -m build` → wrapper artifacts.
- `twine upload dist/librarian_2026-0.9.0*`.
- Smoke test: fresh venv, `pip install librarian-2026`, confirm pip output shows "Installing collected packages: librarian-governance, librarian-2026". `python -c "import librarian; print(librarian.__version__)"` → `0.9.0`.

**Step 3 — update documentation and tooling**
- README.md: replace all `pip install librarian-2026` with `pip install librarian-governance`. Add a prominent "Renamed from librarian-2026" callout at the top.
- `.claude-plugin/plugin.json` + `marketplace.json`: no change required (plugin name is independent of PyPI dist name).
- GitHub release notes: document the rename + backward-compat guarantee.
- Pin the deprecation sunset date: "the `librarian-2026` wrapper will continue to be published through at least 2027-04-22 (one year of overlap)."

**Step 4 — sunset plan for `librarian-2026`**
- Continue publishing wrapper pkgs for each new version through 2027-04-22.
- After sunset: final wrapper version pins `librarian-governance>=X` (no exact match), prints a stronger deprecation notice, and stops being re-published on new releases.
- Never yank older wrapper versions — PEP 541 and general PyPI courtesy both discourage this; it only breaks reproducible builds.

---

## Path A detail — PEP 541 name transfer

Include this section only if the user decides to pursue it.

### Prerequisite outreach (6 weeks minimum)

Contact Nekroze through all three channels over a 6-week window, **keep copies of every message sent**:

1. **Email** `nekroze@eturnilnetwork.com` (the PyPI profile email).
2. **GitHub issue** on `https://github.com/Nekroze/librarian` — polite, non-demanding, outline the intent and ask about the package's future.
3. **Email** any address found in the project's documentation or home page.

Three attempts, minimum 2 weeks apart. Log them in a plaintext file so they can be cited in the PEP 541 request.

### The `pypi-support` issue

After 6 weeks of non-response, open an issue at `https://github.com/pypa/pypi-support/issues/new` using the `PEP 541 Request: librarian` template. Required content:

- **Proof of abandonment**: last release 2013; no activity on GitHub repo since (verify at request time); three documented unanswered contact attempts.
- **Proof of notability of requesting project**: this is the hard part for a new project. Helpful: GitHub stars, download counts, cited adoption. For `librarian-2026` with zero external adoption, this is the bar that will likely cause rejection.
- **Why a fork under a different name is not acceptable**: hardest bar. Realistic honest answer for our case would be "it isn't strictly unacceptable, we just prefer the shorter name" — which is likely to get the request denied.
- **Download statistics for the existing package**: the workgroup pulls these themselves. Card-game-library from 2013 with ~2 releases and no updates likely has near-zero modern downloads, which helps.

### Outcome branches from the PEP 541 decision

- **Approved** — PyPI workgroup transfers ownership of `librarian` to our account. The old Nekroze project's files stay on PyPI (PEP 541: "Projects are never removed from the Package Index solely on the basis of abandonment"), but ownership of the name passes to us. We can then publish new versions as `librarian==0.9.0` and it will supersede Nekroze's 0.3.0 as the latest version. Follow the same wrapper choreography from Path B with `librarian` substituted for `librarian-governance`.
- **Rejected** — fall back to Path B.
- **No response within 60 days** — ping the issue. No response within 120 days — fall back to Path B.

### Why I don't recommend this

The expected-value math is bad for a solo project with no existing external adoption. Spend the time shipping features instead; pursue the rename later from a position of strength if ever needed.

---

## Path C detail — stay on `librarian-2026` permanently

Trivial — no work. Note it permanently in CLAUDE.md so the decision is recorded and not relitigated next session.

**Cost accounting:**
- Aesthetic: name looks dated by 2027.
- Functional: zero. PyPI has plenty of year-stamped package names (`six`, `2to3`, various).
- Reversibility: always can switch to Path B later; one additional rename doesn't change the wrapper math.

Good choice if the user has higher-priority features to ship.

---

## Risks common to all paths

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PyPI account takeover before transfer | Low | High | 2FA enabled on the `ghengis5-git` PyPI account; verify before Path A outreach |
| Someone else registers `librarian-governance` during Path B window | Low | Medium | Reserve the name immediately by uploading a 0.0.0 placeholder under the chosen name as soon as the decision is made |
| Wrapper semantics confusion (user pins `librarian-2026==0.9.0` expecting old behavior, gets new behavior via the redirect) | Medium | Low | Wrapper README + PyPI description explicitly calls out the redirect |
| Deprecation sunset breaks someone's pinned install in 2027 | Low | Medium | Never yank old wrapper versions; pin the sunset date publicly; give 12 months minimum |

---

## Out of scope

- **Claude Code plugin name** — stays `librarian`. The plugin marketplace name is independent of the PyPI dist name. No change required.
- **Python import name** — stays `librarian`. Both wrappers (`librarian-2026` → `librarian-governance`) have `librarian/` as their source package. `import librarian` does not change.
- **GitHub repo name** — stays `ghengis5-git/librarian`. PyPI dist name is independent of the GitHub repo name.
- **v0.8.0 release** — ships as `librarian-2026` per existing plan. This phase does not touch v0.8.0.

---

## Decision required before this phase moves to "in progress"

User picks one of:

- **A**: Pursue PEP 541 for the bare name `librarian`. Accepts 6-12 week timeline, ~50% rejection risk, fallback to B.
- **B** (**recommended**): Rename to `librarian-governance` in v0.9.0. Ship wrapper on `librarian-2026`. Keep the wrapper alive through 2027-04-22.
- **C**: Stay on `librarian-2026`. Update CLAUDE.md to record the decision and move on.

Bundle this decision with the v0.8.0 ship approval, or defer until after v0.8.0 lands — no functional dependency between them.

---

## Acceptance criteria — if Path B is chosen

- `pip install librarian-governance` installs v0.9.0 in a fresh venv.
- `pip install librarian-2026` installs the wrapper + librarian-governance transitively.
- `python -c "import librarian; print(librarian.__version__)"` returns `0.9.0` in both cases.
- `librarian --registry docs/REGISTRY.yaml audit` runs successfully under both install paths.
- README.md and PyPI descriptions clearly state the rename.
- Deprecation sunset date is recorded in at least two public places (README + PyPI description of the wrapper).

---

## Related docs

- `phase-f-plugin-and-release-20260413-V1.1.md` — original namespace decision (Phase F V1.1, where `librarian-2026` was adopted as a fallback).
- `librarian-buildout-plan-20260411-V1.2.md` — buildout plan; §Risks flagged namespace collision.
- `CLAUDE.md` — current state of the project; Phase 8/9 roadmap sits here.
