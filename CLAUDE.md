# CLAUDE.md

## Branches

- Work directly on `main`. Never create branches, including per-session
  `claude/...` branches.
- Only ever push to `main`. Never push to any other branch.

## Git history

`main` is a series of commits on top of upstream OpenMoHAA. Keep that series
clean:

- Never push fix-up or follow-up commits on top. Fold every change into the
  commit that introduced the code it touches, then replay the commits after it.
- Keep each rewritten commit's author and date, and update its message so it
  still describes what the commit does.
- Make sure every rewritten commit still builds and passes the tests, not just
  the final one.
- Push the rewritten `main` with `git push --force-with-lease origin main`.
