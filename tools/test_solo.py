#!/usr/bin/env python3
"""Solo: right-click a legend switch to show only that one; click it again to put the row back.

    python tools/serve.py --no-open     # in another shell
    python tools/test_solo.py

Solo is not a separate filter - it means "everything else in this row off", expressed through the
very switches it appears to override. That is what these checks are really pinning down: that the
legend still shows the truth while a solo is up, that each row is independent, that the rows
compose, and above all that turning a solo off restores the row EXACTLY as it was, including
switches that were already off before anyone soloed anything.

It also guards the reason the design moved: the sphere chip in the sidebar backs out of the current
selection before soloing. A live selection already fades everything outside it to 13%, which is the
same fade the filter uses, so soloing while somebody was selected changed classes and changed
almost no pixels - a bug a class-level test passed clean and only looking caught.
"""
from playwright.sync_api import sync_playwright

FAIL = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("http://localhost:8000/", wait_until="networkidle")
    pg.wait_for_timeout(2600)

    state = lambda: pg.evaluate("""()=>{const ns=window.web.nodes, es=window.web.edges;
        const lit={}; for(const n of ns) if(!n.g.classList.contains('dimmed')) lit[n.p.group]=(lit[n.p.group]||0)+1;
        return {lit, spheres:Object.keys(lit).length,
                litMen:ns.filter(n=>n.p.gender==='m'&&!n.g.classList.contains('dimmed')).length,
                litWomen:ns.filter(n=>n.p.gender==='f'&&!n.g.classList.contains('dimmed')).length,
                shownEdges:es.filter(e=>!e.g.classList.contains('hidden')).length,
                solo:[...document.querySelectorAll('.lgc.solo')].map(x=>x.title),
                off:[...document.querySelectorAll('.lgc')].map(x=>x.getAttribute('aria-pressed')).join(''),
                /* Per-row switch states. "Did soloing one row disturb another" has to be asked of
                   the SWITCHES: soloing women legitimately empties any sphere with no women in it
                   (Wilde alone, Beyond Europe), so counting lit spheres answers a different
                   question and answers it wrongly. */
                rows:(()=>{const t=[...document.querySelectorAll('.lg-title')].map(e=>e.textContent.trim());
                  const out={}; let row=null;
                  for(const el of document.querySelector('#legend').children){
                    if(el.classList.contains('lg-title')){row=el.textContent.trim();out[row]='';}
                    else if(el.classList.contains('lgc')&&row)out[row]+=el.getAttribute('aria-pressed')==='true'?'1':'0';
                  }
                  return out;})(),
                hash:location.hash,
                focusing:document.getElementById('web').classList.contains('focusing')};}""")
    btn = lambda label: [x for x in pg.query_selector_all(".lgc")
                         if label in (x.text_content() or "")][0]
    right = lambda el: (el.click(button="right"), pg.wait_for_timeout(450))

    baseline = state()
    check("liaisons starts switched off (the state a restore must return to)",
          baseline["off"].count("false") == 1, f"{baseline['off'].count('false')} off")

    # ---- the sidebar chip: backs out of the selection, then solos
    pg.evaluate("()=>{location.hash='#/p/douglas'}"); pg.wait_for_timeout(800)
    check("selecting puts the map in focus mode", state()["focusing"])
    pg.click("#ptag"); pg.wait_for_timeout(600)
    s = state()
    check("the chip backs out of the selection first",
          s["hash"] == "" and not s["focusing"], f"hash={s['hash']!r} focusing={s['focusing']}")
    check("the chip narrows to its sphere", s["spheres"] == 1 and "aesthete" in s["lit"], str(s["lit"]))
    check("the mark is on the LEGEND, not the chip", s["solo"] and "Aesthetes" in s["solo"][0],
          str(s["solo"]))

    # ---- clicking the soloed switch restores the row exactly
    btn("Aesthetes").click(); pg.wait_for_timeout(450)
    check("clicking the soloed switch restores the row exactly", state()["off"] == baseline["off"])

    # ---- right-click solos any row: People
    right(btn("1895 trials"))
    s = state()
    check("right-click solos a sphere", s["spheres"] == 1 and "trials" in s["lit"], str(s["lit"]))
    right(btn("1895 trials"))
    check("right-click again restores exactly", state()["off"] == baseline["off"])

    # ---- Gender row, independent of People
    right(btn("Women"))
    s = state()
    check("right-click solos a gender", s["litMen"] == 0 and s["litWomen"] > 0,
          f"men {s['litMen']}, women {s['litWomen']}")
    check("soloing a gender leaves the People switches alone",
          s["rows"]["People"] == baseline["rows"]["People"],
          f"{baseline['rows']['People']} -> {s['rows']['People']}")

    # ---- rows compose
    right(btn("Aesthetes"))
    s = state()
    check("a soloed sphere and a soloed gender compose",
          s["spheres"] == 1 and "aesthete" in s["lit"] and s["litMen"] == 0 and s["litWomen"] > 0,
          f"{s['lit']} men={s['litMen']} women={s['litWomen']}")
    check("both rows show their own mark", len(s["solo"]) == 2, str(s["solo"]))
    right(btn("Aesthetes")); right(btn("Women"))
    check("unwinding both restores exactly", state()["off"] == baseline["off"])

    # ---- Connections row
    before_edges = state()["shownEdges"]
    right(btn("Married"))
    s = state()
    check("right-click solos a connection class", 0 < s["shownEdges"] < before_edges,
          f"{before_edges} -> {s['shownEdges']} edges shown")
    check("soloing a connection leaves the People and Gender switches alone",
          s["rows"]["People"] == baseline["rows"]["People"]
          and s["rows"]["Gender"] == baseline["rows"]["Gender"])
    right(btn("Married"))
    check("restores exactly", state()["off"] == baseline["off"])

    # ---- hand-editing a row ends its solo but keeps what the row now shows
    right(btn("Aesthetes"))
    btn("Society").click(); pg.wait_for_timeout(450)
    s = state()
    check("clicking another switch ends the solo mark", not s["solo"], str(s["solo"]))
    check("...and keeps what the row now shows", "aesthete" in s["lit"] and "society" in s["lit"],
          str(s["lit"]))

    check("no console errors", not errs, str(errs[:3]))
    b.close()

print("\nFAILURES:", FAIL if FAIL else "none")
import sys
sys.exit(1 if FAIL else 0)
