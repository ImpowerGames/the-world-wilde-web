#!/usr/bin/env python3
"""Measure the drawing, so a layout change can be judged by numbers rather than by eye.

    python tools/layout_report.py                 measure and print
    python tools/layout_report.py --save before.json
    ... make a change ...
    python tools/layout_report.py --compare before.json
    python tools/layout_report.py --json          machine-readable, for CI

What it counts:

  crossings      pairs of connections that cross without sharing a person. The headline number.
  nodes on lines people sitting on a connection they are not an endpoint of. A node on a line
                 reads as a junction, implying a relationship that is not in the data.
  overlaps       people drawn on top of each other.
  seed drift     how far the force pass moved each person from where the radial tree seated them.
                 A large median means the tree and the springs disagree, which is usually the
                 real cause when the other numbers are bad.

Why this exists: several layout changes that looked fine on screen measured clearly worse — holding
nodes to their seeded seats took crossings from 27 to 54, and three placement hints turned out to
be costing five crossings. Neither was visible by eye. Measure, then look.

Requires: playwright (`pip install playwright && playwright install chromium`).
The layout is deterministic, so repeated runs on unchanged data give identical numbers.
"""
import argparse
import functools
import http.server
import json
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8791

MEASURE = r"""() => {
  const {nodes, edges} = circle;
  const ccw = (ax,ay,bx,by,cx,cy) => (cy-ay)*(bx-ax) > (by-ay)*(cx-ax);
  const crosses = (e,f) => {
    if (e.a===f.a || e.a===f.b || e.b===f.a || e.b===f.b) return false;
    const a=e.a.x,b=e.a.y,c=e.b.x,d=e.b.y,p=f.a.x,q=f.a.y,r=f.b.x,s=f.b.y;
    return ccw(a,b,p,q,r,s)!==ccw(c,d,p,q,r,s) && ccw(a,b,c,d,p,q)!==ccw(a,b,c,d,r,s);
  };
  const pairs = [];
  const perEdge = new Map(edges.map(e => [e.r.id, 0]));
  for (let i=0;i<edges.length;i++) for (let j=i+1;j<edges.length;j++) {
    if (crosses(edges[i], edges[j])) {
      pairs.push(edges[i].r.id + " x " + edges[j].r.id);
      perEdge.set(edges[i].r.id, perEdge.get(edges[i].r.id)+1);
      perEdge.set(edges[j].r.id, perEdge.get(edges[j].r.id)+1);
    }
  }
  const onLine = [];
  for (const n of nodes) {
    let worst = null;
    for (const e of edges) {
      if (e.a===n || e.b===n) continue;
      const x1=e.a.x,y1=e.a.y,dx=e.b.x-x1,dy=e.b.y-y1,L2=dx*dx+dy*dy||1;
      let t=((n.x-x1)*dx+(n.y-y1)*dy)/L2; t=Math.max(0,Math.min(1,t));
      const d = Math.hypot(n.x-(x1+t*dx), n.y-(y1+t*dy));
      if (d < n.r && (!worst || d < worst.d)) worst = {d, id: e.r.id};
    }
    if (worst) onLine.push({person: n.id, edge: worst.id,
                            into: Math.round((n.r-worst.d)/n.r*100)});
  }
  const overlaps = [];
  for (let i=0;i<nodes.length;i++) for (let j=i+1;j<nodes.length;j++) {
    const a=nodes[i], b=nodes[j];
    if (Math.hypot(b.x-a.x, b.y-a.y) < a.r+b.r) overlaps.push(a.id + " / " + b.id);
  }
  const drifts = nodes.filter(n => n.sx != null)
                      .map(n => ({id: n.id, d: Math.round(Math.hypot(n.x-n.sx, n.y-n.sy))}))
                      .sort((a,b) => b.d - a.d);
  const med = drifts.length ? drifts[drifts.length >> 1].d : 0;
  return {
    people: nodes.length, connections: edges.length,
    crossings: pairs.length, crossingPairs: pairs.slice(0, 12),
    worstEdges: [...perEdge.entries()].filter(e => e[1]).sort((a,b) => b[1]-a[1]).slice(0, 5),
    nodesOnLines: onLine.length, onLineDetail: onLine.slice(0, 8),
    overlaps: overlaps.length, overlapDetail: overlaps.slice(0, 6),
    seedDriftMedian: med, seedDriftWorst: drifts.slice(0, 5),
  };
}"""


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("", PORT), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.5)
    return srv


def measure():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright is needed for this one:\n"
                 "  pip install playwright && playwright install chromium")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit("validation failed — the data has to be valid before the drawing means anything")
    srv = serve()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1440, "height": 950})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://localhost:{PORT}/")
            pg.wait_for_load_state("networkidle")
            pg.wait_for_timeout(4500)          # the settle-in tween, then rest
            if errs:
                sys.exit("the page threw before it could be measured:\n  " + "\n  ".join(errs))
            data = pg.evaluate(MEASURE)
            b.close()
    finally:
        srv.shutdown()
    return data


def show(m):
    print(f"{m['people']} people · {m['connections']} connections\n")
    print(f"  crossings            {m['crossings']}")
    print(f"  nodes on lines       {m['nodesOnLines']}")
    print(f"  node overlaps        {m['overlaps']}")
    print(f"  seed drift (median)  {m['seedDriftMedian']}px")
    if m["worstEdges"]:
        print("\n  most-crossed connections:")
        for eid, n in m["worstEdges"]:
            print(f"    {n:>3}  {eid}")
    if m["onLineDetail"]:
        print("\n  people sitting on a connection they are not part of:")
        for d in m["onLineDetail"]:
            print(f"    {d['person']:22} on {d['edge']:28} {d['into']}% into the node")
    if m["overlapDetail"]:
        print("\n  overlapping people:")
        for o in m["overlapDetail"]:
            print(f"    {o}")
    if m["seedDriftWorst"]:
        worst = ", ".join(f"{d['id']} {d['d']}px" for d in m["seedDriftWorst"])
        print(f"\n  moved furthest from their radial seat: {worst}")


def compare(now, then):
    print("           was  ->  now")
    keys = [("crossings", "crossings"), ("nodesOnLines", "nodes on lines"),
            ("overlaps", "overlaps"), ("seedDriftMedian", "seed drift (median)")]
    worse = False
    for k, label in keys:
        a, b = then.get(k, 0), now.get(k, 0)
        arrow = "  " if a == b else ("better" if b < a else "WORSE")
        if b > a and k != "seedDriftMedian":
            worse = True
        print(f"  {label:22} {a:>5}  ->  {b:<5} {arrow}")
    print("\n" + ("Some numbers went up — worth a look before committing."
                  if worse else "Nothing regressed."))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="print raw JSON")
    ap.add_argument("--save", metavar="FILE", help="write the measurements to a file")
    ap.add_argument("--compare", metavar="FILE", help="diff against a saved file")
    args = ap.parse_args()

    m = measure()
    if args.json:
        print(json.dumps(m, indent=1))
    elif args.compare:
        compare(m, json.loads(Path(args.compare).read_text(encoding="utf-8")))
    else:
        show(m)
    if args.save:
        Path(args.save).write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
        print(f"\nsaved to {args.save}")


main()
