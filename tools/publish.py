#!/usr/bin/env python3
"""Publish this directory to the public repository.

The map is developed inside a larger private repository and published as a standalone one, so
"push" is two unrelated operations: sending the private repo to its own remote, and splitting this
subdirectory into its own history and sending that somewhere else. Forgetting the second is silent
- the private repo looks up to date and the live site quietly serves last week's map. This script
is the second half, so that it is one command rather than three remembered ones.

    python tools/publish.py               validate, split, push
    python tools/publish.py --dry-run     say what it would do, touch nothing
    python tools/publish.py --remote X    push to a different remote
    python tools/publish.py --allow-dirty publish with uncommitted changes present

The prefix is DERIVED, never hardcoded: this file ships to the public repository, and writing the
private repo's directory layout into it would publish that layout for no reason. Run from the
public repo, where this directory IS the root, there is nothing to split and the script says so
and stops.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent.parent
DEFAULT_BRANCH = "main"


def git(*args, cwd=None, check=True):
    r = subprocess.run(["git", *args], cwd=cwd or HERE, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"  git {' '.join(args)}\n  {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def pick_remote(explicit):
    """The remote pointing at the public repository, not the one this repo was cloned from."""
    if explicit:
        return explicit
    remotes = {}
    for line in git("remote", "-v").splitlines():
        name, url = line.split()[0], line.split()[1]
        remotes[name] = url
    if not remotes:
        sys.exit("No git remotes are configured. Add the public repository as a remote first.")
    # The published site's own name is the reliable signal; fall back to asking.
    hits = [n for n, u in remotes.items() if "the-world-wilde-web" in u]
    if len(hits) == 1:
        return hits[0]
    sys.exit("Could not tell which remote is the public repository. Pass --remote NAME.\n"
             + "\n".join(f"  {n}  {u}" for n, u in sorted(remotes.items())))


def main():
    ap = argparse.ArgumentParser(description="Split this directory out and push it to the public repo.")
    ap.add_argument("--remote", help="remote to push to (default: detected)")
    ap.add_argument("--branch", default=DEFAULT_BRANCH, help=f"branch on the remote (default: {DEFAULT_BRANCH})")
    ap.add_argument("--dry-run", action="store_true", help="report, change nothing")
    ap.add_argument("--allow-dirty", action="store_true", help="publish with uncommitted changes present")
    a = ap.parse_args()

    root = Path(git("rev-parse", "--show-toplevel"))
    prefix = HERE.relative_to(root).as_posix() if HERE != root else ""
    if not prefix:
        sys.exit("This IS the published repository - there is nothing to split out of it.\n"
                 "Push it the ordinary way: git push origin " + a.branch)

    # A split publishes COMMITTED history. Uncommitted work is silently left behind, which reads
    # as "I published that" when you did not, so it stops here by default.
    dirty = git("status", "--porcelain", "--", str(HERE))
    if dirty and not a.allow_dirty:
        n = len(dirty.splitlines())
        sys.exit(f"{n} uncommitted change(s) in this directory. A split publishes committed history "
                 f"only, so these would NOT reach the site.\nCommit them, or pass --allow-dirty if "
                 f"you meant to publish without them.")

    remote = pick_remote(a.remote)
    print(f"  prefix   {prefix}")
    print(f"  remote   {remote} -> {a.branch}")

    # Validate before publishing rather than after. CI would catch a broken corpus, but only once
    # it is already the public repo's problem.
    print("  checking the corpus ...")
    r = subprocess.run([sys.executable, str(HERE / "tools/validate.py"), "--check"],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout.strip() + "\n\nValidation failed - nothing was pushed.")
    print("  corpus ok")

    if a.dry_run:
        print("  --dry-run: stopping before the split")
        return 0

    print("  splitting (walks the history; slow the first time, cached after) ...")
    sha = git("subtree", "split", f"--prefix={prefix}", cwd=root)
    if not sha:
        sys.exit("The split produced no commit.")
    print(f"  split    {sha[:10]}")

    # Push a BRANCH, never the bare sha: git cannot set up tracking for a detached object and
    # reports that failure as a fatal error even though the objects transferred fine.
    local = f"publish/{a.branch}"
    git("branch", "-f", local, sha, cwd=root)
    out = subprocess.run(["git", "push", remote, f"{local}:refs/heads/{a.branch}"],
                         cwd=root, capture_output=True, text=True)
    print((out.stderr or out.stdout).strip())
    if out.returncode:
        sys.exit("\nPush failed. If it was rejected as non-fast-forward, the public repo has a "
                 "commit this split does not know about - most likely an edit made on GitHub. "
                 "Bring that back into this repo first; do not force.")
    print(f"\nPublished. The Pages workflow rebuilds the site from {a.branch}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
