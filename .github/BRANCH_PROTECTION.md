# Branch protection for `main`

Branch protection is configured in the GitHub UI (not in this repository). After **CI** is green on the default branch, apply these settings for [rainiur/sentinel](https://github.com/rainiur/sentinel) (or your fork).

## Steps

1. Open **Settings** → **Branches** → **Add branch protection rule** (or edit the existing rule for `main`).
2. **Branch name pattern:** `main`
3. Enable:
   - **Require a pull request before merging** (optional but recommended for teams).
   - **Require status checks to pass before merging**
     - Search and enable: **API**, **Web**, **Docker Compose (config)**, **Docker images (build)** — names match the `name:` fields in `.github/workflows/ci.yml`.
   - **Require branches to be up to date before merging** (recommended if you use PRs).
4. Optional hardening:
   - **Require linear history**
   - **Do not allow bypassing the above settings** for admins (if your org policy allows).
   - **Lock branch** only for release-only workflows.

## Notes

- Status checks appear after at least **one successful run** of the workflow on `main` (e.g. push the workflow file and let CI complete).
- If you rename jobs in `ci.yml`, update the selected checks in the protection rule.
