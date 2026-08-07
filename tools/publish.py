#!/usr/bin/env python3
"""Publish this directory to the public repository.

The map is developed inside a larger private repository and published as a standalone one, so
"push" is two unrelated operations: sending the private repo to its own remote, and getting this
subdirectory into a different repo. Forgetting the second is silent - the private repo looks up to
date and the live site quietly serves last week's map. This script is the second half.

    python tools/publish.py               validate, mirror, push
    python tools/publish.py --dry-run     say what it would do, touch nothing
    python tools/publish.py --remote X    push to a different remote
    python tools/publish.py --allow-dirty publish with uncommitted changes present

WHY NOT `git subtree split`: it re-walks the whole history of the prefix on every run. Its cache
is `$GIT_DIR/subtree-cache/$$` - keyed on the process id and deleted when the process exits - so
it never carries anything between invocations and never gets faster, however many times you run
it. This instead keeps a checkout of the public repo, copies the current directory over it and
commits the difference: the cost is the number of CHANGED FILES, not the length of the history.

The published history is therefore one commit per publish rather than a rewrite of the private
repo's commits. That is deliberate - the public repo is meant to carry the map, not a log of how
the map got made.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent.parent
DEFAULT_BRANCH = "main"
# Inside .git/, which git itself never tracks and no tool of ours walks.
MIRROR_NAME = "publish-mirror"


def git(*args, cwd, check=True, quiet=False):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"  git {' '.join(args)}\n  {(r.stderr or r.stdout).strip()}")
    return r.stdout.strip()


def pick_remote(explicit, root):
    if explicit:
        return explicit
    remotes = {}
    for line in git("remote", "-v", cwd=root).splitlines():
        parts = line.split()
        remotes[parts[0]] = parts[1]
    if not remotes:
        sys.exit("No git remotes are configured. Add the public repository as a remote first.")
    hits = [n for n, u in remotes.items() if "the-world-wilde-web" in u]
    if len(hits) == 1:
        return hits[0]
    sys.exit("Could not tell which remote is the public repository. Pass --remote NAME.\n"
             + "\n".join(f"  {n}  {u}" for n, u in sorted(remotes.items())))


def mirror_contents(src, dst):
    """Make dst's tree identical to src, leaving dst/.git alone."""
    for p in dst.iterdir():
        if p.name == ".git":
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    for p in src.iterdir():
        if p.name in (".git", "__pycache__"):
            continue
        if p.is_dir():
            shutil.copytree(p, dst / p.name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(p, dst / p.name)


def main():
    ap = argparse.ArgumentParser(description="Mirror this directory into the public repo and push.")
    ap.add_argument("--remote", help="remote to push to (default: detected)")
    ap.add_argument("--branch", default=DEFAULT_BRANCH, help=f"branch (default: {DEFAULT_BRANCH})")
    ap.add_argument("--dry-run", action="store_true", help="report, change nothing")
    ap.add_argument("--allow-dirty", action="store_true", help="publish with uncommitted changes")
    ap.add_argument("--message", help="commit message for the published commit")
    ap.add_argument("--mode", choices=("mirror", "subtree"), default="mirror",
                    help="mirror (default, ~0.3s): one commit per publish. "
                         "subtree (~1 min): replays this directory's private commits one by one.")
    a = ap.parse_args()

    root = Path(git("rev-parse", "--show-toplevel", cwd=HERE))
    if HERE == root:
        sys.exit("This IS the published repository - there is nothing to mirror into it.\n"
                 f"Push it the ordinary way: git push origin {a.branch}")

    # A publish takes what is ON DISK. Uncommitted work would go out without being recorded
    # privately first, which is the wrong way round, so it stops here by default.
    dirty = git("status", "--porcelain", "--", str(HERE), cwd=root)
    if dirty and not a.allow_dirty:
        sys.exit(f"{len(dirty.splitlines())} uncommitted change(s) here. Commit them first so the "
                 f"private repo records what was published, or pass --allow-dirty.")

    remote = pick_remote(a.remote, root)
    url = git("remote", "get-url", remote, cwd=root)
    print(f"  source   {HERE.relative_to(root).as_posix()}")
    print(f"  remote   {remote} -> {a.branch}")

    print("  checking the corpus ...")
    r = subprocess.run([sys.executable, str(HERE / "tools/validate.py"), "--check"],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout.strip() + "\n\nValidation failed - nothing was pushed.")
    print("  corpus ok")

    if a.dry_run:
        print(f"  --dry-run: stopping before the {a.mode}")
        return 0

    if a.mode == "subtree":
        # Replays this directory's private commits as their own history in the public repo. Slow
        # and unavoidably so - subtree's cache is keyed on the process id and deleted on exit, so
        # it re-walks the whole prefix history every run and never gets faster.
        print("  splitting (re-walks the whole history; expect about a minute) ...")
        sha = git("subtree", "split", f"--prefix={HERE.relative_to(root).as_posix()}", cwd=root)
        if not sha:
            sys.exit("The split produced no commit.")
        local = f"publish/{a.branch}"
        # Push a BRANCH, never the bare sha: git cannot set up tracking for a detached object and
        # reports that failure as fatal even though the objects transferred fine.
        git("branch", "-f", local, sha, cwd=root)
        out = subprocess.run(["git", "push", remote, f"{local}:refs/heads/{a.branch}"],
                             cwd=root, capture_output=True, text=True)
        print((out.stderr or out.stdout).strip())
        if out.returncode:
            sys.exit("\nPush failed. If it was rejected as non-fast-forward, the public repo has "
                     "commits this split does not contain - which is what happens once other "
                     "people are merging pull requests there. Use the default --mode mirror, "
                     "which builds on top of them instead; do not force.")
        print(f"\nPublished {sha[:10]}. The Pages workflow rebuilds the site.")
        return 0

    mirror = Path(git("rev-parse", "--git-dir", cwd=root))
    mirror = (root / mirror if not mirror.is_absolute() else mirror) / MIRROR_NAME
    if not (mirror / ".git").exists():
        print("  first run: cloning the public repo (once) ...")
        mirror.parent.mkdir(parents=True, exist_ok=True)
        if mirror.exists():
            shutil.rmtree(mirror)
        # autocrlf off: the mirror's working copy must match the repository byte for byte. With
        # Windows' default, a line-ending flip would stage every text file at once and publish a
        # 300-file commit that changed nothing anyone can see.
        git("clone", "--config", "core.autocrlf=false", "--branch", a.branch,
            url, str(mirror), cwd=root)
    else:
        git("remote", "set-url", "origin", url, cwd=mirror)
        git("fetch", "origin", a.branch, cwd=mirror)
        git("checkout", "-B", a.branch, f"origin/{a.branch}", cwd=mirror)

    mirror_contents(HERE, mirror)
    git("add", "-A", cwd=mirror)
    if not git("status", "--porcelain", cwd=mirror):
        print("  nothing to publish - the public repo already matches this directory.")
        return 0

    changed = len(git("status", "--porcelain", cwd=mirror).splitlines())
    subject = a.message or git("log", "-1", "--pretty=%s", "--", str(HERE), cwd=root) or "update"
    git("commit", "-m", subject, cwd=mirror)
    out = subprocess.run(["git", "push", "origin", a.branch], cwd=mirror,
                         capture_output=True, text=True)
    print((out.stderr or out.stdout).strip())
    if out.returncode:
        sys.exit("\nPush failed. If it was rejected as non-fast-forward, the public repo has a "
                 "commit this mirror has not seen - most likely an edit made on GitHub. Run again "
                 "to fetch it, then re-publish; do not force.")
    print(f"\nPublished {changed} changed path(s). The Pages workflow rebuilds the site.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
