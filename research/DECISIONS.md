# DECISIONS — branch strategy, push policy (reversible, docs-only)

1. **Work on dedicated local branch `research/audit-1587497` (base `1587497`).** HEAD `1587497` is 2 behind `origin/main`; do not rebase/merge unless a plan explicitly authorizes it.
2. **No push, no PR.** Out-of-scope per task: no `git push`, no PR creation, no remote mutation.
3. **Local branch for any future code:** if code work is later approved, create a local feature branch from the recorded HEAD; keep `research/**` docs-only and separable.
4. **No history rewrite.** Do not amend `1587497` or earlier; do not touch tags (`v0.1.0` lightweight stays as-is).
5. **Reversibility:** full revert of this task = `rm -rf research/` (new dir only; nothing else was touched).
