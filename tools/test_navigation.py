#!/usr/bin/env python3
"""Exercise every navigation gesture and assert what it must and must not do.

    python tools/serve.py --no-open     # in another shell
    python tools/test_navigation.py

The thing being guarded is not "does it pan" but "does it pan WITHOUT moving anybody" - the whole
point of a dedicated pan button on a web this dense is that a slightly-off aim must not silently
edit the layout. It also pins down two things that are invisible by eye:

  * a pure two-finger drag must not change the zoom at all. It did, by 12%, because the gesture's
    reference separation was captured one move after the second finger landed.
  * every zoom must keep the viewBox on the PANE's aspect ratio, not on W:H. The wheel did not,
    which letterboxed the drawing the moment anyone scrolled.

Both were found by asserting on numbers, not by looking - the failure modes are a few per cent and
no screenshot would have shown them. Looking is still what caught the layout faults; these are the
complement to it, not a replacement.

Requires: playwright (`pip install playwright && playwright install chromium`), and the site
served at localhost:8000.
"""
from playwright.sync_api import sync_playwright

FAIL = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 1000}, has_touch=True)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("http://localhost:8000/", wait_until="networkidle")
    pg.wait_for_timeout(2800)

    vb = lambda: [float(x) for x in pg.evaluate(
        "document.getElementById('web').getAttribute('viewBox')").split()]
    node = lambda i: pg.evaluate(
        "i=>{const n=window.circle.nodes.find(n=>n.id===i);return [Math.round(n.x),Math.round(n.y)];}", i)
    # a person sitting under the opening frame, to right-drag ON TOP OF
    target = pg.evaluate("""()=>{const v=document.getElementById('web').getAttribute('viewBox').split(' ').map(Number);
        const r=document.getElementById('web').getBoundingClientRect();
        const n=window.circle.nodes.find(n=>n.id==='wilde');
        return {id:n.id, cx:r.left+(n.x-v[0])/v[2]*r.width, cy:r.top+(n.y-v[1])/v[3]*r.height};}""")

    # ---- right-drag ON a node: pans, does not move the node
    before_vb, before_n = vb(), node(target["id"])
    pg.mouse.move(target["cx"], target["cy"])
    pg.mouse.down(button="right")
    pg.mouse.move(target["cx"] - 160, target["cy"] - 90, steps=8)
    pg.mouse.up(button="right")
    pg.wait_for_timeout(200)
    after_vb, after_n = vb(), node(target["id"])
    check("right-drag pans", abs(after_vb[0] - before_vb[0]) > 20,
          f"vb.x {before_vb[0]:.0f} -> {after_vb[0]:.0f}")
    check("right-drag on a person does NOT move them", after_n == before_n,
          f"{before_n} -> {after_n}")
    check("right-drag does not pin them",
          not pg.evaluate("()=>window.circle.nodes.find(n=>n.id==='wilde').pinned"))

    # ---- context menu suppressed
    cm = pg.evaluate("""()=>{const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true});
        document.getElementById('web').dispatchEvent(e); return e.defaultPrevented;}""")
    check("contextmenu default prevented on the map", cm)

    # ---- middle-drag pans
    before_vb = vb()
    pg.mouse.move(target["cx"], target["cy"])
    pg.mouse.down(button="middle")
    pg.mouse.move(target["cx"] + 140, target["cy"] + 70, steps=8)
    pg.mouse.up(button="middle")
    pg.wait_for_timeout(200)
    check("middle-drag pans", abs(vb()[0] - before_vb[0]) > 20)

    # ---- right-click alone must not clear a selection
    pg.evaluate("()=>{location.hash='#/p/wilde';}")
    pg.wait_for_timeout(700)
    pg.mouse.move(300, 700)
    pg.mouse.down(button="right"); pg.mouse.up(button="right")
    pg.wait_for_timeout(300)
    check("a right-click does not clear the selection", pg.evaluate("()=>location.hash") == "#/p/wilde",
          pg.evaluate("()=>location.hash"))
    pg.evaluate("()=>{location.hash='';}"); pg.wait_for_timeout(400)

    # ---- wheel zoom keeps the pane aspect (the bug: it rebuilt the box from W:H)
    pane = pg.evaluate("""()=>{const r=document.getElementById('web').getBoundingClientRect();
        return r.width/r.height;}""")
    pg.mouse.move(500, 600); pg.mouse.wheel(0, -240); pg.wait_for_timeout(200)
    v = vb()
    check("wheel zoom preserves the pane aspect", abs(v[2] / v[3] - pane) < 0.02,
          f"vb {v[2]/v[3]:.3f} vs pane {pane:.3f}")

    # ---- two-finger drag pans without changing scale, and moves nobody
    before_vb, before_n = vb(), node("wilde")
    pg.evaluate("""()=>{
      const el=document.getElementById('web');
      const mk=(t,id,x,y)=>el.dispatchEvent(new PointerEvent(t,{pointerId:id,pointerType:'touch',
        clientX:x,clientY:y,bubbles:true,cancelable:true,isPrimary:id===1}));
      mk('pointerdown',1,400,500); mk('pointerdown',2,500,500);
      for(let s=1;s<=10;s++){ mk('pointermove',1,400-s*12,500-s*8); mk('pointermove',2,500-s*12,500-s*8); }
      mk('pointerup',1,280,420); mk('pointerup',2,380,420);
    }""")
    pg.wait_for_timeout(200)
    after_vb, after_n = vb(), node("wilde")
    check("two-finger drag pans", abs(after_vb[0] - before_vb[0]) > 20,
          f"vb.x {before_vb[0]:.0f} -> {after_vb[0]:.0f}")
    check("two-finger drag keeps the scale", abs(after_vb[2] - before_vb[2]) < 1,
          f"w {before_vb[2]:.0f} -> {after_vb[2]:.0f}")
    check("two-finger drag moves nobody", after_n == before_n)

    # ---- pinch zooms
    before_vb = vb()
    pg.evaluate("""()=>{
      const el=document.getElementById('web');
      const mk=(t,id,x,y)=>el.dispatchEvent(new PointerEvent(t,{pointerId:id,pointerType:'touch',
        clientX:x,clientY:y,bubbles:true,cancelable:true,isPrimary:id===1}));
      mk('pointerdown',1,450,500); mk('pointerdown',2,550,500);
      for(let s=1;s<=10;s++){ mk('pointermove',1,450-s*10,500); mk('pointermove',2,550+s*10,500); }
      mk('pointerup',1,350,500); mk('pointerup',2,650,500);
    }""")
    pg.wait_for_timeout(200)
    check("pinch out zooms in", vb()[2] < before_vb[2] - 20,
          f"w {before_vb[2]:.0f} -> {vb()[2]:.0f}")

    # ---- left-drag on empty space still pans, left-drag on a node still moves them
    # Find ground that is empty RIGHT NOW: the view has been zoomed and panned by the tests above,
    # so a point verified as empty at load time may well be sitting on somebody by this point.
    empty = pg.evaluate("""()=>{
        for(let x=140;x<900;x+=37)for(let y=300;y<900;y+=37){
          const el=document.elementFromPoint(x,y);
          if(el&&el.id==='web')return {x,y};
        }
        return null;}""")
    check("found empty ground to drag from", bool(empty), str(empty))
    before_vb = vb()
    pg.mouse.move(empty["x"], empty["y"]); pg.mouse.down()
    pg.mouse.move(empty["x"] + 110, empty["y"] - 50, steps=6); pg.mouse.up()
    pg.wait_for_timeout(200)
    check("left-drag on empty ground still pans", abs(vb()[0] - before_vb[0]) > 10,
          f"vb.x {before_vb[0]:.0f} -> {vb()[0]:.0f}")

    # Moving somebody is a HELD gesture now. A press that drags straight away is a pan - which is the
    # point of the change, since on a web this dense you are usually starting on somebody - and only
    # a press that survives the hold picks the person up.
    def at(nid):
        return pg.evaluate("""id=>{const v=document.getElementById('web').getAttribute('viewBox').split(' ').map(Number);
            const r=document.getElementById('web').getBoundingClientRect();
            const n=window.circle.nodes.find(n=>n.id===id);
            return {cx:r.left+(n.x-v[0])/v[2]*r.width, cy:r.top+(n.y-v[1])/v[3]*r.height};}""", nid)

    t2, before_n, before_vb = at("wilde"), node("wilde"), vb()
    pg.mouse.move(t2["cx"], t2["cy"]); pg.mouse.down()
    pg.mouse.move(t2["cx"] + 40, t2["cy"] + 30, steps=6); pg.mouse.up()
    pg.wait_for_timeout(250)
    check("left-drag on a person pans instead of moving them", node("wilde") == before_n)
    check("...and that drag panned the view", abs(vb()[0] - before_vb[0]) > 10,
          f"vb.x {before_vb[0]:.0f} -> {vb()[0]:.0f}")

    t2, before_n = at("wilde"), node("wilde")
    pg.mouse.move(t2["cx"], t2["cy"]); pg.mouse.down()
    pg.wait_for_timeout(650)                      # past LONGPRESS_MS
    armed = pg.evaluate("()=>!!document.querySelector('#web .node.armed')")
    pg.mouse.move(t2["cx"] + 40, t2["cy"] + 30, steps=6); pg.mouse.up()
    pg.wait_for_timeout(250)
    check("holding a person arms the drag", armed)
    check("held drag moves them", node("wilde") != before_n)
    check("the armed mark is cleared on release",
          not pg.evaluate("()=>!!document.querySelector('#web .node.armed')"))

    # ...and the same hold, released without travelling, puts them back
    t2 = at("wilde")
    pg.mouse.move(t2["cx"], t2["cy"]); pg.mouse.down()
    pg.wait_for_timeout(650); pg.mouse.up()
    pg.wait_for_timeout(600)
    home = pg.evaluate("()=>{const n=window.circle.nodes.find(n=>n.id==='wilde');return [n.cx,n.cy];}")
    now = node("wilde")
    check("a hold released in place sends them home",
          abs(now[0] - home[0]) < 2 and abs(now[1] - home[1]) < 2, f"{now} vs {home}")

    check("no console errors", not errs, str(errs[:3]))
    b.close()

print("\nFAILURES:", FAIL if FAIL else "none")
