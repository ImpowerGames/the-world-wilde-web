"use strict";

async function loadWeb() {
  const r = await fetch("data/web.json", { cache: "no-cache" });
  if (!r.ok)
    throw new Error(
      "could not load data/web.json (" +
        r.status +
        "). " +
        "If you opened this file directly, serve it instead: python tools/serve.py",
    );
  return r.json();
}
(async function boot() {
  let WEB;
  try {
    WEB = await loadWeb();
  } catch (err) {
    document.querySelector("#emptymsg").hidden = false;
    document.querySelector("#emptymsg").textContent = err.message;
    console.error(err);
    return;
  }

  const $ = (s) => document.querySelector(s);
  const MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const esc = (s) =>
    String(s ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  // Emphasis markup in quote fields, parsed after esc(): *italics*, **bold**,
  // _underline_, __double underline__, ~~strikethrough~~. Only well-formed pairs
  // render; a stray marker is left literal rather than mangling the text.
  //
  // The double underline is drawn as one, not as some heavier substitute. It is a mark the
  // writer actually made and the Complete Letters explicitly discard - "no indication is given
  // of the occasional words which have more than one underlining" - so where the manuscript has
  // been read, this is the only place that degree survives. __ must be tried before _, or the
  // single-underline rule eats the inner pair and strands the outer markers.
  function fmtEmphasis(s) {
    return String(s ?? "")
      .replace(/\*\*([^*\n]+)\*\*/g, "<b>$1</b>")
      .replace(/\*([^*\n]+)\*/g, "<i>$1</i>")
      .replace(/__([^_\n]+)__/g, '<u class="u2">$1</u>')
      .replace(/_([^_\n]+)_/g, "<u>$1</u>")
      .replace(/~~([^~\n]+)~~/g, "<s>$1</s>");
  }
  function sortKey(d) {
    if (!d || d.y == null) return Infinity;
    return d.y + ((d.m ?? 6.5) - 1) / 12 + (d.d ?? 15) / 372;
  }
  function fmtOne(d, withYear) {
    const y = withYear ? ` ${d.y}` : "";
    if (d.d && d.m) return `${d.d} ${MONTHS[d.m - 1]}${y}`;
    if (d.m) return `${MONTHS[d.m - 1]}${y}`;
    return withYear ? String(d.y) : "";
  }
  function fmtDate(d) {
    if (!d || d.y == null) return "date unknown";
    if (d.label) return (d.circa ? "c. " : "") + d.label;
    const c = d.circa ? "c. " : "";
    const t = d.to;
    if (t && t.y != null && !(t.y === d.y && t.m === d.m && t.d === d.d)) {
      if (t.y === d.y) {
        if (d.m && t.m === d.m && d.d && t.d)
          return `${c}${d.d}–${t.d} ${MONTHS[d.m - 1]} ${d.y}`;
        if (d.m && t.m && !d.d && !t.d)
          return `${c}${MONTHS[d.m - 1]}–${MONTHS[t.m - 1]} ${d.y}`;
        return `${c}${fmtOne(d, false) || d.y} – ${fmtOne(t, false) || t.y} ${d.y}`;
      }
      return `${c}${fmtOne(d, true)} – ${fmtOne(t, true)}`;
    }
    return c + (fmtOne(d, true) || String(d.y));
  }
  // A letter's dating, built from its acts. There is no stored wording any more: the volume's
  // hedging IS the structure — `inferred` is its brackets, `uncertain` its question mark, `circa`
  // its "circa", `part` its "early"/"late", and `weekday` the day-name Wilde wrote, which sits
  // OUTSIDE the brackets because the day is his and the date is the editors'. Every one of the 33
  // transcriptions round-trips through this character for character, which is what let the stored
  // string be dropped.
  // A letter's dating, built from its acts. The volume's own wording is NOT reproduced: that was
  // how the structure was proved complete enough to stop storing the string, not a display goal.
  // Nothing cites this line, so it says what it means instead of what the editors printed.
  //
  //   Written 8 September 1900 · Postmarked 9 September 1900
  //   Written circa 30 June 1894
  //   Received 2 July 1891
  //
  // `inferred` is deliberately absent: it records that the date is not ON the document but was
  // the reader says so below the letter. `circa` and `uncertain` stay - dropping them would put
  // the date more confidently than the source does.
  function fmtDatePart(d, withYear) {
    if (!d) return "";
    if (d.season) return withYear ? `${d.season} ${d.y}` : d.season;
    if (!d.m) return withYear && d.y != null ? String(d.y) : "";
    const y = withYear && d.y != null ? ` ${d.y}` : "";
    return `${d.d ? d.d + " " : ""}${d.part && !d.d ? d.part + " " : ""}${MONTHS[d.m - 1]}${y}`;
  }
  function fmtDating(d) {
    if (!d) return "";
    let core = fmtDatePart(d, true);
    // A RANGE. Same year and the year is said once at the end: "March–April 1891". The date
    // schema has carried `to` all along for `evidence_date`; 65 letters in the volume need it.
    const t = d.to;
    if (t && !(t.y === d.y && t.m === d.m && t.d === d.d)) {
      core =
        t.y === d.y
          ? `${fmtDatePart(d, false) || d.y}–${fmtDatePart(t, true) || t.y}`
          : `${fmtDatePart(d, true) || d.y}–${fmtDatePart(t, true) || t.y}`;
    }
    if (!core) core = d.weekday ? "" : "date unknown";
    if (d.circa) core = "circa " + core;
    if (d.weekday) core = `${d.weekday[0].toUpperCase()}${d.weekday.slice(1)}${core ? " " + core : ""}`;
    if (d.uncertain) core += " (?)";
    return core;
  }
  // Lowercase: the dating is a clause inside the header sentence — "Wilde to Ives, postmarked
  // 21 March 1898, Paris" — and a capital mid-clause reads as a mistake. Anything showing an act
  // standalone can capitalise it there.
  const ACT_LABEL = { written: "written", sent: "sent", postmarked: "postmarked",
                      received: "received" };
  function fmtLetterDating(t) {
    return ["written", "sent", "postmarked", "received"]
      .filter((a) => (t[a] || {}).date)
      .map((a) => {
        const act = t[a];
        let s = `${ACT_LABEL[a]} ${fmtDating(act.date)}`.trim();
        if (act.time) s += ` at ${act.time}`;
        return s;
      })
      .join(" · ");
  }
  function yearOf(d) {
    return d && d.y != null ? String(d.y) : "?";
  }
  function relDateLabel(r) {
    if (r.date_label) return r.date_label;
    const a = fmtDate(r.start);
    if (!r.end || r.end.y == null) return a;
    const b = fmtDate(r.end);
    return a === b ? a : `${a} – ${b}`;
  }
  function mulberry32(a) {
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const CERT_LABEL = {
    "self-reported": "Self-Reported",
    "second-hand": "Second-Hand",
    uncorroborated: "Uncorroborated",
    married: "Married",
    "attraction-expressed": "Attraction expressed",
    platonic: "Platonic",
  };
  const OUTCOME_LABEL = {
    declined: "declined",
    unknown: "outcome unknown",
    unreciprocated: "not reciprocated",
  };
  const DEFAULT_OFF = new Set([]);
  // Verified carries no chip: only the states that need a reader's attention show one.
  const VER_META = {
    "verified-exact": ["", ""],
    "verified-elision": ["", ""],
    "needs-fix": ["! Needs fix", "v-warn"],
    rejected: ["✗ Rejected", "v-bad"],
    unverified: ["⧖ Pending verification", "v-pend"],
  };
  const HOW_LABEL = {
    "photo-reproduction": "read in a photographic reproduction",
    "text-layer": "read from an extracted text layer, not at the page",
    "in-hand": "read in the physical copy",
    "as-published": "read as published",
    unverified: "",
  };
  // What is being quoted, where that differs from the work it was read in. `hand` marks the
  // documents somebody wrote out, which are the only ones with an original left to check:
  // a printed pamphlet has nothing behind the print.
  // [singular for the chip, written by hand, plural for the filter's option list]. The plurals
  // are spelled out because two of them are irregular and one of them is not a plural at all:
  // court evidence is "Testimony" however much of it there is.
  const DOC_META = {
    letter: ["Letter", true, "Letters"],
    telegram: ["Telegram", true, "Telegrams"],
    postcard: ["Postcard", true, "Postcards"],
    diary: ["Diary", true, "Diaries"],
    inscription: ["Inscription", true, "Inscriptions"],
    manuscript: ["Manuscript", true, "Manuscripts"],
    memoir: ["Memoir", false, "Memoirs"],
    testimony: ["Testimony", false, "Testimony"],
    plea: ["Plea", false, "Pleas"],
    verdict: ["Verdict", false, "Verdicts"],
    interview: ["Interview", false, "Interviews"],
    pamphlet: ["Pamphlet", false, "Pamphlets"],
    novel: ["Novel", false, "Novels"],
    essay: ["Essay", false, "Essays"],
    poem: ["Poem", false, "Poems"],
    typescript: ["Typescript", false, "Typescripts"],
    biography: ["Biography", false, "Biographies"],
    study: ["Study", false, "Studies"],
    article: ["Article", false, "Articles"],
    encyclopedia: ["Encyclopedia entry", false, "Encyclopedia entries"],
    "editorial-note": ["Editorial note", false, "Editorial notes"],
    introduction: ["Introduction", false, "Introductions"],
    "finding-aid": ["Finding aid", false, "Finding aids"],
    "web-page": ["Web page", false, "Web pages"],
  };
  const howLabel = (h) => (h in HOW_LABEL ? HOW_LABEL[h] : h || "");
  const GROUP_LABEL = {
    core: "Wilde",
    family: "Spouse",
    society: "Society",
    aesthete: "Aesthetes",
    trials: "1895 trials",
    chaeronea: "Chaeronea",
    later: "Later circle",
    liaisons: "Outside the circle",
    beyond: "Beyond Europe",
  };

  const P = new Map(WEB.people.map((p) => [p.id, p]));
  const RELS = WEB.relationships.filter((r) =>
    r.people.every((id) => P.has(id)),
  );
  const byPerson = new Map();
  for (const r of RELS)
    for (const id of r.people) {
      if (!byPerson.has(id)) byPerson.set(id, []);
      byPerson.get(id).push(r);
    }
  const degree = (id) => (byPerson.get(id) || []).length;
  // Platonic records draw no line and take no part in the layout: the map treats them
  // as unconnected, so layout forces and rendered edges come from MAP_RELS. The panels,
  // lists and pair view still use RELS, because the records are real.
  const MAP_RELS = RELS.filter((r) => r.certainty !== "platonic");
  const mapByPerson = new Map();
  for (const r of MAP_RELS)
    for (const id of r.people) {
      if (!mapByPerson.has(id)) mapByPerson.set(id, []);
      mapByPerson.get(id).push(r);
    }
  const mapDegree = (id) => (mapByPerson.get(id) || []).length;

  function shortLabel(p) {
    const s = shortLabelRaw(p);
    return p.name_is_descriptor ? "“" + s + "”" : s;
  }
  function shortLabelRaw(p) {
    let sur = (p.sort_name || p.name).split(",")[0].trim();
    // long double-barrelled surnames overrun their neighbours; keep the first element
    if (sur.length > 13 && sur.includes("-")) sur = sur.split("-")[0];
    if (sur.length > 15) sur = sur.slice(0, 14) + "…";
    const clash = WEB.people.some(
      (o) =>
        o.id !== p.id && (o.sort_name || o.name).split(",")[0].trim() === sur,
    );
    if (!clash) return sur;

    const first =
      (p.name || "")
        .split(/\s+/)
        .find(
          (w) =>
            !/^(sir|lord|lady|dame|rev|revd|mr|mrs|miss|ms|dr|capt|captain|admiral|col|colonel|gen|general|hon)\.?$/i.test(
              w,
            ),
        ) || "";
    return `${sur} ${first ? first[0] + "." : ""}`.trim();
  }
  function partnerOf(r, id) {
    return r.people[0] === id ? r.people[1] : r.people[0];
  }
  function verCounts() {
    let ok = 0,
      pend = 0,
      total = 0,
      pointers = 0;
    for (const r of RELS)
      for (const q of r.sources || []) {
        total++;
        if ((q.quote || "") === "") pointers++;
        if (
          q.verification === "verified-exact" ||
          q.verification === "verified-elision"
        )
          ok++;
        else pend++;
      }
    return { ok, pend, total, pointers };
  }

  const W = 1200,
    H = 800;
  const SIM = {
    K_REP: 36000,
    K_SPRING: 0.035,
    REST: 150,
    K_CENTER: 0.02,
    DAMP: 0.85,
    MAX_V: 14,
    ALPHA0: 1,
    ALPHA_DECAY: 0.004,
    ALPHA_MIN: 0.02,
    PAD: 14,
  };
  const CLEAR = 13,
    MAX_SHOVE = 7; // clearance from unconnected lines; per-tick displacement cap
  const KEEPOUT = 120; // clearance a connectionless person keeps from any cluster member
  const LABEL_BELOW = 15,
    LABEL_H = 13,
    LABEL_PAD = 3,
    LABEL_CH = 3.0;
  function fitLabelBoxes() {
    for (const n of nodes) {
      const w = shortLabel(n.p).length * LABEL_CH * 2;
      n.hw = Math.max(n.r, w / 2 + LABEL_PAD); // half-width of disc+label
      n.hh = (n.r + LABEL_BELOW + LABEL_PAD) / 2 + n.r / 2; // half-height of the combined box
      n.oy = (LABEL_BELOW + LABEL_PAD) / 2; // box centre sits this far below the node centre
    }
  }

  function boxPush(a, b, pad, apply) {
    const dx = b.x - a.x,
      dy = b.y + b.oy - (a.y + a.oy);
    const ox = a.hw + b.hw + pad - Math.abs(dx),
      oyv = a.hh + b.hh + pad - Math.abs(dy);
    if (ox <= 0 || oyv <= 0) return 0;
    if (ox < oyv) {
      const s = ((dx < 0 ? -1 : 1) * ox) / 2;
      apply(-s, 0, s, 0);
      return ox;
    }
    const s = ((dy < 0 ? -1 : 1) * oyv) / 2;
    apply(0, -s, 0, s);
    return oyv;
  }
  const rand = mulberry32(0x57196f);

  const nodes = WEB.people.map((p) => ({
    id: p.id,
    p,
    r: 16 + 3 * Math.sqrt(mapDegree(p.id)),
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    pinned: false,
    hx: (p.layout && p.layout.x) ?? null,
    hy: (p.layout && p.layout.y) ?? null,
  }));
  nodes.sort((a, b) => mapDegree(b.id) - mapDegree(a.id));
  nodes.forEach((n, i) => {
    const ang = i * 2.39996,
      rad = 30 + 16 * Math.sqrt(i) * 4;
    n.x = W / 2 + Math.cos(ang) * rad + rand() * 8;
    n.y = H / 2 + Math.sin(ang) * rad + rand() * 8; // circular; see below
    if (n.hx != null) {
      n.x = n.hx;
      n.y = n.hy;
    }
  });
  const N = new Map(nodes.map((n) => [n.id, n]));

  const HUB = nodes.reduce((a, b) =>
    mapDegree(a.id) >= mapDegree(b.id) ? a : b,
  );
  const edges = MAP_RELS.map((r) => ({
    r,
    a: N.get(r.people[0]),
    b: N.get(r.people[1]),
  }));

  for (const e of edges) {
    const leaf =
      (mapByPerson.get(e.a.id) || []).length === 1 ||
      (mapByPerson.get(e.b.id) || []).length === 1;
    e.rest = leaf ? SIM.REST * 0.58 : SIM.REST;
    e.k = leaf ? SIM.K_SPRING * 2.4 : SIM.K_SPRING;
  }

  const compOf = new Map(),
    compHome = new Map(),
    compSoft = new Set();
  let mainComp = 0;
  {
    const components = (useAll) => {
      const map = new Map();
      let c = 0;
      for (const n of nodes) {
        if (map.has(n.id)) continue;
        map.set(n.id, c);
        const stack = [n.id];
        while (stack.length) {
          const id = stack.pop();
          for (const r of mapByPerson.get(id) || []) {
            if (!useAll && DEFAULT_OFF.has(r.certainty)) continue;
            const o = partnerOf(r, id);
            if (!map.has(o)) {
              map.set(o, c);
              stack.push(o);
            }
          }
        }
        c++;
      }
      return map;
    };
    const full = components(true); // true connectivity
    const vis = components(false); // what the eye sees at rest
    for (const [k, v] of vis) compOf.set(k, v);
    const size = new Map();
    for (const [, ci] of compOf) size.set(ci, (size.get(ci) || 0) + 1);
    const ranked = [...size.entries()].sort((a, b) => b[1] - a[1]);
    mainComp = ranked.length ? ranked[0][0] : 0;
    const SLOTS = [
      [185, 175],
      [185, 625],
      [1015, 175],
      [1015, 625],
      [600, 100],
      [600, 705],
      [390, 120],
      [810, 120],
    ];
    const memberOf = new Map();
    for (const n of nodes) {
      if (!memberOf.has(compOf.get(n.id))) memberOf.set(compOf.get(n.id), n);
    }
    const leadOnly = []; // singletons held only by a hidden link
    let s = 0,
      solo = 0;
    ranked.forEach(([ci, sz], idx) => {
      if (idx === 0) {
        compHome.set(ci, [W / 2, H / 2]);
        return;
      }
      if (sz > 1 && s < SLOTS.length) {
        compHome.set(ci, SLOTS[s++]);
        return;
      }
      if (mapDegree(memberOf.get(ci).id)) {
        leadOnly.push(ci);
        compHome.set(ci, null);
        return;
      }
      // No recorded connection at all.
      const side = solo % 2 ? W - 70 : 70,
        row = Math.floor(solo / 2);
      compHome.set(ci, [side, 285 + row * 115]);
      solo++;
    });
    // A person attached only by a attraction-expressed link still belongs beside whoever they
    // are attached to, so borrow that person's territory rather than drifting to centre.
    for (const ci of leadOnly) {
      const n = memberOf.get(ci);
      const anchor = [...full]
        .filter(([id, f]) => f === full.get(n.id) && id !== n.id)
        .map(([id]) => compHome.get(compOf.get(id)))
        .find(Boolean);
      if (anchor) {
        compHome.set(ci, anchor);
        compSoft.add(ci);
      }
    }
    for (const n of nodes) {
      // start satellites at home so they don't migrate across
      const home = compHome.get(compOf.get(n.id));
      if (home && compOf.get(n.id) !== mainComp) {
        n.x = home[0] + (rand() - 0.5) * 70;
        n.y = home[1] + (rand() - 0.5) * 70;
      }
    }

    {
      const hub = nodes.reduce((a, b) =>
        mapDegree(a.id) >= mapDegree(b.id) ? a : b,
      );
      const inMain = (id) => compOf.get(id) === mainComp;
      const kids = new Map(),
        depth = new Map([[hub.id, 0]]),
        order = [hub.id];
      for (let i = 0; i < order.length; i++) {
        const id = order[i];
        kids.set(id, []);
        for (const r of mapByPerson.get(id) || []) {
          const o = partnerOf(r, id);
          if (!inMain(o) || depth.has(o)) continue; // chords land back on a placed node: skip
          depth.set(o, depth.get(id) + 1);
          kids.get(id).push(o);
          order.push(o);
        }
      }
      const leaves = new Map(); // angular weight = leaf count of the subtree
      for (let i = order.length - 1; i >= 0; i--) {
        const id = order[i],
          ch = kids.get(id) || [];
        leaves.set(
          id,
          ch.length ? ch.reduce((s, c) => s + leaves.get(c), 0) : 1,
        );
      }

      const angleOf = new Map();
      const RING = [0, 150, 255, 340, 410];
      const layout = () => {
        const place = (id, a0, a1) => {
          angleOf.set(id, (a0 + a1) / 2);
          const ch = (kids.get(id) || []).slice();
          if (ch.length > 1 && angleOf.size > 1) {
            const bary = (c) => {
              const xs = [];
              for (const r of mapByPerson.get(c) || []) {
                const o = partnerOf(r, c);
                if (
                  o !== id &&
                  angleOf.has(o) &&
                  !(kids.get(c) || []).includes(o)
                )
                  xs.push(angleOf.get(o));
              }
              return xs.length
                ? xs.reduce((a, b) => a + b, 0) / xs.length
                : null;
            };
            const keyed = ch.map((c) => [c, bary(c)]);
            if (keyed.some((k) => k[1] != null))
              keyed.sort(
                (A, B) => (A[1] ?? (a0 + a1) / 2) - (B[1] ?? (a0 + a1) / 2),
              );
            ch.length = 0;
            for (const [c] of keyed) ch.push(c);
            kids.set(id, ch);
          }
          let a = a0;
          for (const c of ch) {
            const w = ((a1 - a0) * leaves.get(c)) / leaves.get(id);
            place(c, a, a + w);
            a += w;
          }
        };
        place(hub.id, -Math.PI / 2, Math.PI * 1.5);
      };
      layout();
      layout(); // second pass: the barycentres are better informed
      for (const [id, mid] of angleOf) {
        const d = depth.get(id),
          rad =
            RING[Math.min(d, RING.length - 1)] +
            (d >= RING.length ? (d - RING.length + 1) * 70 : 0);
        const n = N.get(id);
        n.x = W / 2 + Math.cos(mid) * rad;
        n.y = H / 2 + Math.sin(mid) * rad;
      }
      for (const n of nodes)
        if (compOf.get(n.id) === mainComp) {
          n.sx = n.x;
          n.sy = n.y;
          n.seedDepth = depth.get(n.id);
        }
      for (const n of nodes)
        if (n.hx != null) {
          n.x = n.hx;
          n.y = n.hy;
        } // hints still win
    }
  }
  let alpha = SIM.ALPHA0,
    running = false,
    raf = 0;
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  function tick() {
    for (const n of nodes) {
      n.fx = 0;
      n.fy = 0;
    }
    for (let i = 0; i < nodes.length; i++)
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i],
          b = nodes[j];
        let dx = a.x - b.x,
          dy = a.y - b.y,
          d2 = dx * dx + dy * dy;
        let d = Math.sqrt(d2) || 0.01;
        if (d < 8) {
          d = 8;
          d2 = 64;
        }
        // push harder between people in different components so territories stay distinct
        const f =
            (SIM.K_REP / d2) *
            (compOf.get(a.id) !== compOf.get(b.id) ? 1.8 : 1),
          fx = (f * dx) / d,
          fy = (f * dy) / d;
        a.fx += fx;
        a.fy += fy;
        b.fx -= fx;
        b.fy -= fy;
      }
    for (const e of edges) {
      const dx = e.b.x - e.a.x,
        dy = e.b.y - e.a.y,
        d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const f = e.k * (d - e.rest),
        fx = (f * dx) / d,
        fy = (f * dy) / d;
      e.a.fx += fx;
      e.a.fy += fy;
      e.b.fx -= fx;
      e.b.fy -= fy;
    }
    for (const n of nodes) {
      const home = compHome.get(compOf.get(n.id));
      if (home && compOf.get(n.id) !== mainComp) {
        // satellite: hold its own territory
        // a person held only by a hidden link gets a gentle nudge toward their anchor's
        // ground, not a hard tether - the spring to that person does the real work
        const k = compSoft.has(compOf.get(n.id)) ? 0.01 : 0.055;
        n.fx += (home[0] - n.x) * k;
        n.fy += (home[1] - n.y) * k;
      } else {
        const pull = SIM.K_CENTER * Math.sqrt(mapDegree(n.id) + 1);
        n.fx += (W / 2 - n.x) * pull * 0.05;
        n.fy += (H / 2 - n.y) * pull * 0.05;
      }
    }
    for (const n of nodes) {
      if (n.pinned) continue;
      n.vx = (n.vx + n.fx * alpha) * SIM.DAMP;
      n.vy = (n.vy + n.fy * alpha) * SIM.DAMP;
      const v = Math.hypot(n.vx, n.vy);
      if (v > SIM.MAX_V) {
        n.vx *= SIM.MAX_V / v;
        n.vy *= SIM.MAX_V / v;
      }
      n.x += n.vx;
      n.y += n.vy;
    }
    for (let pass = 0; pass < 2; pass++)
      for (let i = 0; i < nodes.length; i++)
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i],
            b = nodes[j];
          boxPush(a, b, SIM.PAD * 0.5, (axd, ayd, bxd, byd) => {
            if (!a.pinned) {
              a.x += axd;
              a.y += ayd;
            }
            if (!b.pinned) {
              b.x += bxd;
              b.y += byd;
            }
          });
        }
    for (const n of nodes) {
      // placement hints pull far harder than the centring force
      if (n.hx == null || n.pinned) continue;
      n.vx += (n.hx - n.x) * 0.1;
      n.vy += (n.hy - n.y) * 0.1;
    }
    if (!HUB.pinned && HUB.hx == null) {
      // hold the hub in the middle; everything else arranges around it
      HUB.vx += (W / 2 - HUB.x) * 0.12;
      HUB.vy += (H / 2 - HUB.y) * 0.12;
    }
    // Keep every node clear of lines it is NOT an endpoint of: a node sitting on a
    // line reads as a junction, implying a connection that isn't in the data.
    for (const n of nodes) {
      if (n.pinned) continue;
      let ax = 0,
        ay = 0;
      for (const e of edges) {
        if (e.a === n || e.b === n) continue; // its own connections may touch it
        const x1 = e.a.x,
          y1 = e.a.y,
          dx = e.b.x - x1,
          dy = e.b.y - y1,
          L2 = dx * dx + dy * dy || 1;
        let t = ((n.x - x1) * dx + (n.y - y1) * dy) / L2;
        t = Math.max(0, Math.min(1, t));
        const px = x1 + t * dx,
          py = y1 + t * dy;
        const ox = n.x - px,
          oy = n.y - py,
          d = Math.hypot(ox, oy) || 0.01;
        const min = n.r + CLEAR;
        if (d < min) {
          ax += (ox / d) * (min - d);
          ay += (oy / d) * (min - d);
        }
      }
      if (!ax && !ay) continue;
      let sx = ax * 0.5,
        sy = ay * 0.5; // half the correction; the rest next tick
      const mag = Math.hypot(sx, sy);
      if (mag > MAX_SHOVE) {
        sx *= MAX_SHOVE / mag;
        sy *= MAX_SHOVE / mag;
      }
      n.x += sx;
      n.y += sy;
    }
    alpha -= SIM.ALPHA_DECAY;
  }
  function loop() {
    if (alpha <= SIM.ALPHA_MIN) {
      running = false;
      return;
    }
    tick();
    render();
    raf = requestAnimationFrame(loop);
  }
  function reheat(a) {
    alpha = Math.max(alpha, a);
    if (!running && !reduceMotion) {
      running = true;
      raf = requestAnimationFrame(loop);
    }
    if (reduceMotion) {
      for (let i = 0; i < 300; i++) tick();
      render();
    }
  }

  const svg = $("#web"),
    gE = $("#gEdges"),
    gN = $("#gNodes"),
    tip = $("#tip");
  const NS = "http://www.w3.org/2000/svg";
  function mk(t, attrs, parent) {
    const el = document.createElementNS(NS, t);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(el);
    return el;
  }
  for (const e of edges) {
    const g = mk(
      "g",
      {
        class: `edge cert-${e.r.certainty}${e.r.outcome ? " out-" + e.r.outcome : ""}`,
        "data-id": e.r.id,
      },
      gE,
    );
    e.under = mk("path", { class: "e-under" }, g);
    e.main = mk("path", { class: "e-main" }, g);
    e.hit = mk("path", { class: "e-hit" }, g);
    e.g = g;
    e.hit.addEventListener("pointerenter", (ev) => {
      if (ev.pointerType !== "mouse") return;
      const [pa, pb] = e.r.people.map((id) => P.get(id));
      tip.innerHTML = `<b>${esc(pa.name)} — ${esc(pb.name)}</b><br>${esc(relDateLabel(e.r))} · ${esc(CERT_LABEL[e.r.certainty])}`;
      tip.style.display = "block";
      moveTip(ev);
    });
    e.hit.addEventListener("pointermove", moveTip);
    e.hit.addEventListener("pointerleave", () => (tip.style.display = "none"));
  }
  function moveTip(ev) {
    const wrap = $("#webwrap").getBoundingClientRect();
    let x = ev.clientX - wrap.left + 14,
      y = ev.clientY - wrap.top + 10;
    tip.style.left = Math.min(x, wrap.width - tip.offsetWidth - 8) + "px";
    tip.style.top = Math.min(y, wrap.height - tip.offsetHeight - 8) + "px";
  }

  const PORTRAITS = WEB.portraits || {};
  const defs = $("#web defs") || mk("defs", {}, $("#web")); // reuse the one in the markup
  for (const n of nodes) {
    const g = mk(
      "g",
      {
        class: `node g-${n.p.group}`,
        "data-id": n.id,
        tabindex: "0",
        role: "button",
        "aria-label": `${n.p.name}, open profile`,
      },
      gN,
    );
    const s = n.r * 1.78;
    if (n.p.gender === "m") {
      mk(
        "rect",
        { class: "shape", x: -s / 2, y: -s / 2, width: s, height: s, rx: 2 },
        g,
      );
    } else {
      const c = mk("circle", { class: "shape", r: n.r }, g);
      if (n.p.gender !== "f") c.setAttribute("stroke-dasharray", "3 3");
    }
    const por = PORTRAITS[n.id];
    if (por) {
      const cid = "clip-" + n.id,
        cp = mk("clipPath", { id: cid }, defs);
      if (n.p.gender === "m")
        mk("rect", { x: -s / 2, y: -s / 2, width: s, height: s, rx: 2 }, cp);
      else mk("circle", { r: n.r }, cp);
      const im = mk(
        "image",
        {
          class: "portrait",
          "clip-path": `url(#${cid})`,
          x: -s / 2,
          y: -s / 2,
          width: s,
          height: s,
          preserveAspectRatio: "xMidYMin slice",
        },
        g,
      );

      im.addEventListener("load", () => im.classList.add("loaded"), {
        once: true,
      });
      im.setAttribute("href", por.file);
      im.setAttributeNS("http://www.w3.org/1999/xlink", "href", por.file);
      g.insertBefore(im, g.firstChild); // behind the shape, so its stroke stays the ring
      g.classList.add("has-portrait");
    }
    mk("circle", { class: "pin", r: 3, cy: -n.r }, g);
    const t = mk("text", { y: n.r + LABEL_BELOW }, g);
    t.textContent = shortLabel(n.p);
    n.t = t;
    n.ly = n.r + LABEL_BELOW;
    n.g = g;
    g.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        location.hash = `#/p/${n.id}`;
      }
    });
  }
  fitLabelBoxes();

  function trimPastLabel(n, dx, dy, base) {
    return base;
  }
  function render() {
    for (const e of edges) {
      const d = `M${e.a.x.toFixed(1)},${e.a.y.toFixed(1)}L${e.b.x.toFixed(1)},${e.b.y.toFixed(1)}`;

      const arrow = e.r.certainty === "attraction-expressed" && e.r.direction;
      const src = arrow && e.r.direction === e.b.id ? e.b : e.a,
        tgt = src === e.a ? e.b : e.a;
      const dx = tgt.x - src.x,
        dy = tgt.y - src.y,
        len = Math.hypot(dx, dy) || 1;
      const ux = dx / len,
        uy = dy / len;
      let ts = trimPastLabel(src, ux, uy, src.r); // clear the disc AND the name under it
      let tt = trimPastLabel(tgt, -ux, -uy, tgt.r + (arrow ? 11 : 0)); // leave room for the head too
      if (len <= ts + tt + 6) {
        ts = src.r;
        tt = tgt.r + (arrow ? 11 : 0);
      }

      let dm;
      if (len <= ts + tt + 2) {
        // nodes overlapping: nothing sane to draw between them
        dm = "";
      } else {
        dm =
          `M${(src.x + ux * ts).toFixed(1)},${(src.y + uy * ts).toFixed(1)}` +
          `L${(tgt.x - ux * tt).toFixed(1)},${(tgt.y - uy * tt).toFixed(1)}`;
      }
      e.main.setAttribute("d", dm);
      e.hit.setAttribute("d", d);
      if (e.r.certainty === "married") e.under.setAttribute("d", dm);
    }
    for (const n of nodes)
      n.g.setAttribute(
        "transform",
        `translate(${n.x.toFixed(1)},${n.y.toFixed(1)})`,
      );
  }

  const vb = { x: 0, y: 0, w: W, h: H };

  const ZOOM_OUT_MAX = 6;

  const SCALE_MIN = 0.35,
    LN_MIN = Math.log(SCALE_MIN),
    LN_SPAN = Math.log(ZOOM_OUT_MAX) - LN_MIN;
  const zoomRange = $("#zoomRange");
  let sliderDriving = false; // set while the slider itself is the one zooming
  const sliderToScale = (v) => Math.exp(LN_MIN + (1 - v / 1000) * LN_SPAN);
  const scaleToSlider = (s) =>
    Math.round((1 - (Math.log(s) - LN_MIN) / LN_SPAN) * 1000);
  function syncZoomSlider() {
    if (zoomRange && !sliderDriving)
      zoomRange.value = String(
        Math.max(0, Math.min(1000, scaleToSlider(vb.w / W))),
      );
  }
  function applyVB() {
    svg.setAttribute("viewBox", `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
    syncZoomSlider();
  }
  function clientToWorld(cx, cy) {
    const r = svg.getBoundingClientRect();
    return [
      vb.x + ((cx - r.left) / r.width) * vb.w,
      vb.y + ((cy - r.top) / r.height) * vb.h,
    ];
  }

  function zoomAbout(scale, cx, cy) {
    scale = Math.max(0.35, Math.min(ZOOM_OUT_MAX, scale));
    const [wx, wy] = clientToWorld(cx, cy);
    const nw = W * scale,
      nh = nw / paneAspect();
    vb.x = wx - ((wx - vb.x) * nw) / vb.w;
    vb.y = wy - ((wy - vb.y) * nh) / vb.h;
    vb.w = nw;
    vb.h = nh;
    applyVB();
  }
  let drag = null; // {node,dx,dy,sx,sy,t0,moved} or {pan:true,...}
  const pointers = new Map(); // every finger/pen currently down, for pinch and two-finger pan

  const PAN_BUTTON = (ev) => ev.button === 1 || ev.button === 2;

  function beginPinch() {
    if (pointers.size !== 2) return;
    const pts = [...pointers.values()];
    const mx = (pts[0][0] + pts[1][0]) / 2,
      my = (pts[0][1] + pts[1][1]) / 2;
    const [wx, wy] = clientToWorld(mx, my);
    svg._pinch = {
      d: Math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]),
      w: [wx, wy],
      vb: { ...vb },
    };
  }
  svg.addEventListener("contextmenu", (ev) => ev.preventDefault()); // right-drag must not open the menu

  let killContextMenu = false;
  addEventListener(
    "contextmenu",
    (ev) => {
      if (killContextMenu) {
        ev.preventDefault();
        killContextMenu = false;
      }
    },
    true,
  );

  const LONGPRESS_MS = 450,
    LONGPRESS_SLOP = 8;

  function armNodeDrag() {
    const d = drag;
    if (!d || d.armed || !d.cand) return;
    const [wx, wy] = clientToWorld(d.lastX, d.lastY);
    d.armed = true;
    d.pan = false;
    d.node = d.cand;
    d.dx = d.cand.x - wx;
    d.dy = d.cand.y - wy;
    d.armX = d.lastX;
    d.armY = d.lastY;
    d.cand.g.classList.add("armed");
    svg.classList.remove("panning");
    if (navigator.vibrate) navigator.vibrate(10); // a real phone confirms the hold; ignored elsewhere
  }
  function disarmNodeDrag() {
    if (!drag) return;
    if (drag.timer) {
      clearTimeout(drag.timer);
      drag.timer = 0;
    }
    if (drag.cand) drag.cand.g.classList.remove("armed");
  }
  svg.addEventListener("auxclick", (ev) => {
    if (PAN_BUTTON(ev)) ev.preventDefault();
  });
  svg.addEventListener("mousedown", (ev) => {
    if (ev.button === 1) ev.preventDefault();
  }); // no autoscroll
  svg.addEventListener("pointerdown", (ev) => {
    stopVBTween(); // a hand on the map always beats an animation of it
    pointers.set(ev.pointerId, [ev.clientX, ev.clientY]);
    if (pointers.size > 1) {
      drag = null;
      beginPinch();
      return;
    }
    const panning = PAN_BUTTON(ev);
    const nodeEl = panning ? null : ev.target.closest(".node");
    const [wx, wy] = clientToWorld(ev.clientX, ev.clientY);
    if (nodeEl) {
      const n = N.get(nodeEl.getAttribute("data-id"));
      killContextMenu = false;
      drag = {
        pan: true,
        btn: ev.button,
        px: ev.clientX,
        py: ev.clientY,
        sx: ev.clientX,
        sy: ev.clientY,
        lastX: ev.clientX,
        lastY: ev.clientY,
        t0: performance.now(),
        moved: 0,
        cand: n,
        armed: false,
      };
      drag.timer = setTimeout(armNodeDrag, LONGPRESS_MS);
      svg.setPointerCapture(ev.pointerId);
    } else {
      const edgeEl = panning ? null : ev.target.closest(".edge");
      killContextMenu = false; // a fresh press disarms any suppression left over from the last one
      drag = {
        pan: true,
        btn: ev.button,
        px: ev.clientX,
        py: ev.clientY,
        sx: ev.clientX,
        sy: ev.clientY,
        t0: performance.now(),
        moved: 0,
        edge: edgeEl ? edgeEl.getAttribute("data-id") : null,
      };
      svg.classList.add("panning");
      svg.setPointerCapture(ev.pointerId);
    }
  });
  svg.addEventListener("pointermove", (ev) => {
    if (pointers.has(ev.pointerId))
      pointers.set(ev.pointerId, [ev.clientX, ev.clientY]);

    if (pointers.size === 2) {
      const pts = [...pointers.values()];
      const d = Math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]);
      const mx = (pts[0][0] + pts[1][0]) / 2,
        my = (pts[0][1] + pts[1][1]) / 2;
      if (!svg._pinch) beginPinch();
      const p = svg._pinch;
      if (!p) return;
      const scale = Math.max(
        0.35,
        Math.min(ZOOM_OUT_MAX, (p.vb.w / W) * (p.d / Math.max(d, 1))),
      );
      const r = svg.getBoundingClientRect();
      vb.w = W * scale;
      vb.h = vb.w / paneAspect();
      vb.x = p.w[0] - ((mx - r.left) / r.width) * vb.w;
      vb.y = p.w[1] - ((my - r.top) / r.height) * vb.h;
      applyVB();
      return;
    }
    if (!drag) return;
    drag.lastX = ev.clientX;
    drag.lastY = ev.clientY;
    drag.moved = Math.max(
      drag.moved,
      Math.hypot(ev.clientX - drag.sx, ev.clientY - drag.sy),
    );

    if (!drag.armed && drag.timer && drag.moved > LONGPRESS_SLOP) {
      clearTimeout(drag.timer);
      drag.timer = 0;
      drag.cand = null;
    }
    if (drag.node) {
      const [wx, wy] = clientToWorld(ev.clientX, ev.clientY);
      drag.node.x = wx + drag.dx;
      drag.node.y = wy + drag.dy;
      drag.node.vx = 0;
      drag.node.vy = 0;

      if (drag.moved > 3) {
        drag.node.pinned = true;
        drag.node.g.classList.add("pinned");
      }
      render();
    } else if (drag.pan) {
      const r = svg.getBoundingClientRect();
      vb.x -= ((ev.clientX - drag.px) / r.width) * vb.w;
      vb.y -= ((ev.clientY - drag.py) / r.height) * vb.h;
      drag.px = ev.clientX;
      drag.py = ev.clientY;
      applyVB();
    }
  });
  function endPointer(ev) {
    pointers.delete(ev.pointerId);
    if (pointers.size < 2) svg._pinch = null;
    svg.classList.remove("panning");
    if (!drag) return;
    if (drag.pan && drag.btn === 2) killContextMenu = true; // see the contextmenu note above
    const quick = drag.moved < 6 && performance.now() - drag.t0 < 350;

    if (drag.armed && drag.node) {
      const stayed =
        Math.hypot(drag.lastX - drag.armX, drag.lastY - drag.armY) < 6;
      if (stayed && drag.node.pinned) returnHome(drag.node);
    } else if (drag.cand && quick) location.hash = `#/p/${drag.cand.id}`;
    else if (drag.edge && quick) location.hash = `#/r/${drag.edge}`;
    disarmNodeDrag();

    if (drag.pan && !drag.cand && !drag.edge && quick && !drag.btn) {
      if (location.hash) location.hash = "";
    }
    drag = null;
  }
  svg.addEventListener("pointerup", endPointer);
  svg.addEventListener("pointercancel", endPointer);

  function returnHome(n) {
    n.pinned = false;
    n.g.classList.remove("pinned");
    if (n.cx == null) {
      render();
      return;
    }
    const x0 = n.x,
      y0 = n.y,
      dx = n.cx - x0,
      dy = n.cy - y0;
    if (Math.hypot(dx, dy) < 0.5 || reduceMotion) {
      n.x = n.cx;
      n.y = n.cy;
      render();
      return;
    }
    const t0 = performance.now(),
      DUR = 280;
    (function step() {
      const t = Math.min(1, (performance.now() - t0) / DUR),
        e = 1 - Math.pow(1 - t, 3); // ease out
      n.x = x0 + dx * e;
      n.y = y0 + dy * e;
      render();
      if (t < 1) requestAnimationFrame(step);
    })();
  }

  svg.addEventListener(
    "wheel",
    (ev) => {
      ev.preventDefault();
      stopVBTween();
      zoomAbout(
        (vb.w / W) * (ev.deltaY > 0 ? 1.12 : 0.89),
        ev.clientX,
        ev.clientY,
      );
    },
    { passive: false },
  );

  const legend = $("#legend");
  const groupsInData = [...new Set(WEB.people.map((p) => p.group))];
  const groupOrder = [
    "core",
    "aesthete",
    "trials",
    "society",
    "family",
    "chaeronea",
    "later",
    "beyond",
    "liaisons",
  ].filter((g) => groupsInData.includes(g));

  const SAMPLES = {
    married:
      '<line x1="1" y1="5" x2="33" y2="5" stroke="var(--edge)" stroke-width="5"/><line x1="1" y1="5" x2="33" y2="5" stroke="var(--paper)" stroke-width="1.8"/>',
    "self-reported":
      '<line x1="1" y1="5" x2="33" y2="5" stroke="var(--edge)" stroke-width="1.8"/>',
    "second-hand":
      '<line x1="1" y1="5" x2="33" y2="5" stroke="var(--edge)" stroke-width="1.8" stroke-dasharray="7 5"/>',
    uncorroborated:
      '<line x1="1" y1="5" x2="33" y2="5" stroke="var(--edge)" stroke-width="1.7" stroke-dasharray="1 7" stroke-linecap="round"/>',
    "attraction-expressed":
      '<line x1="1" y1="5" x2="27" y2="5" stroke="var(--edge)" stroke-width="1.6" stroke-dasharray="2 3 6 3"/><path d="M27,1.5 L33,5 L27,8.5 z" fill="var(--edge)"/>',
  };
  function lineSvg(line) {
    return `<svg class="lsample" width="34" height="10" aria-hidden="true">${line || ""}</svg>`;
  }
  function lineSample(c) {
    const line = SAMPLES[c];
    if (!line) {
      return "";
    }
    return lineSvg(line);
  }
  const certOrder = [
    "married",
    "self-reported",
    "second-hand",
    "uncorroborated",
    "attraction-expressed",
    "platonic",
    "none",
  ].filter((c) => RELS.some((r) => r.certainty === c));
  const DEFAULT_OFF_GROUPS = new Set(["liaisons"]);
  const offGroups = new Set(),
    offCerts = new Set();

  const AXES = Object.create(null);
  const soloKey = Object.create(null),
    soloPrev = Object.create(null);
  function registerAxis(name, keys, off, label, title) {
    AXES[name] = { keys, off, btns: new Map(), label, title };
  }
  function syncAxis(name) {
    const a = AXES[name];
    if (!a) return;
    for (const [k, b] of a.btns) {
      const on = soloKey[name] === k;
      b.setAttribute("aria-pressed", String(!a.off.has(k)));
      b.classList.toggle("solo", on);
      b.title = on
        ? `Showing only ${a.label(k)} — click to bring the rest back`
        : a.title(k);
    }
  }
  function toggleSolo(name, key) {
    const a = AXES[name];
    if (!a) return;
    if (soloKey[name] === key) {
      a.off.clear();
      for (const k of soloPrev[name] || []) a.off.add(k);
      soloKey[name] = null;
    } else {
      soloPrev[name] = new Set(a.off);
      a.off.clear();
      for (const k of a.keys) if (k !== key) a.off.add(k);
      soloKey[name] = key;
    }
    syncAxis(name);
    applyFilters();
  }
  function lgBtn(name, key, html) {
    const a = AXES[name];
    const b = document.createElement("button");
    b.className = "lgc";
    b.innerHTML = html;
    a.btns.set(key, b);
    b.addEventListener("click", () => {
      if (soloKey[name] === key) {
        toggleSolo(name, key);
        return;
      }
      if (a.off.has(key)) a.off.delete(key);
      else a.off.add(key);
      soloKey[name] = null; // hand-editing a row ends its solo; the row keeps what it is now
      syncAxis(name);
      applyFilters();
    });
    b.addEventListener("contextmenu", (ev) => {
      ev.preventDefault();
      toggleSolo(name, key);
    });
    legend.appendChild(b);
    return b;
  }

  legend.addEventListener("contextmenu", (ev) => ev.preventDefault());
  const SOLO_HINT = " · right-click to show only this";
  if (groupOrder.length) {
    const t = document.createElement("span");
    t.className = "lg-title";
    t.textContent = "Sphere";
    legend.appendChild(t);
    registerAxis(
      "group",
      groupOrder,
      offGroups,
      (g) => GROUP_LABEL[g] || g,
      (g) =>
        (DEFAULT_OFF_GROUPS.has(g)
          ? `Show ${GROUP_LABEL[g] || g} (hidden by default)`
          : `Toggle ${GROUP_LABEL[g] || g}`) + SOLO_HINT,
    );
    for (const g of groupOrder) {
      if (DEFAULT_OFF_GROUPS.has(g)) offGroups.add(g);
      lgBtn(
        "group",
        g,
        `<span class="dot" style="background:var(--g-${g})"></span>${esc(GROUP_LABEL[g] || g)}`,
      );
    }
    syncAxis("group");
    const sep = document.createElement("span");
    sep.className = "lg-sep";
    legend.appendChild(sep);
  }
  const offGenders = new Set();
  {
    const t = document.createElement("span");
    t.className = "lg-title";
    t.textContent = "Gender";
    legend.appendChild(t);
    const GLABEL = { m: "men", f: "women" };
    registerAxis(
      "gender",
      ["m", "f"],
      offGenders,
      (k) => GLABEL[k],
      (k) => `Toggle ${GLABEL[k]}` + SOLO_HINT,
    );
    lgBtn(
      "gender",
      "m",
      `<svg width="12" height="12" aria-hidden="true"><rect x="1.5" y="1.5" width="9" height="9" rx="1" fill="none" stroke="var(--ink2)" stroke-width="1.5"/></svg>Men`,
    );
    lgBtn(
      "gender",
      "f",
      `<svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="none" stroke="var(--ink2)" stroke-width="1.5"/></svg>Women`,
    );
    syncAxis("gender");
    const br = document.createElement("span");
    br.className = "lg-break";
    legend.appendChild(br);
  }
  if (certOrder.length) {
    const t = document.createElement("span");
    t.className = "lg-title";
    t.textContent = "Connections";
    legend.appendChild(t);

    registerAxis(
      "cert",
      certOrder,
      offCerts,
      (c) => CERT_LABEL[c],
      (c) =>
        (DEFAULT_OFF.has(c)
          ? `Show ${CERT_LABEL[c]} connections (hidden by default)`
          : `Toggle ${CERT_LABEL[c]}`) + SOLO_HINT,
    );
    for (const c of certOrder) {
      if (DEFAULT_OFF.has(c)) offCerts.add(c);
      lgBtn("cert", c, `${lineSample(c)}${esc(CERT_LABEL[c])}`);
    }
    syncAxis("cert");
  }
  let searchTerm = "";
  let searchScope = Array.from($("#searchscope").options).find(
    (option) => option.defaultSelected,
  )?.value;

  const NAME_TEXT = new Map(),
    QUOTE_TEXT = new Map(),
    NOTE_TEXT = new Map();
  {
    const push = (m, id, s) => {
      if (s) m.set(id, (m.get(id) || "") + " " + String(s).toLowerCase());
    };
    for (const p of WEB.people) {
      push(
        NAME_TEXT,
        p.id,
        `${p.name} ${(p.aka || []).join(" ")} ${p.sort_name || ""}`,
      );
      push(QUOTE_TEXT, p.id, p.bio);
      push(
        NOTE_TEXT,
        p.id,
        [
          p.bio_note,
          p.roster_note,
          ...(p.sexuality_sources || []).flatMap((ce) => [
            ce.subject,
            ce.note,
            ce.date_label,
            ce.period,
          ]),
        ]
          .filter(Boolean)
          .join("  "),
      );
    }
    for (const r of RELS) {
      const bits = [r.summary];

      for (const q of r.sources || [])
        bits.push(q.quote, q.translation, q.context, q.supports);
      const blob = bits.filter(Boolean).join("  ");
      const d = r.disputed || {};
      const notes = [
        r.certainty_reasoning,
        r.date_label,
        r.sources_order_note,
        r.prior_class,
        d.claim,
        d.asserted_by,
        d.disputed_by,
        d.grounds,
        ...(r.null_findings || []).map((n) =>
          typeof n === "string" ? n : JSON.stringify(n),
        ),
        ...(r.sources || []).flatMap((q) => [
          q.citation_provenance,
          q.translation_note,
          q.locator,
          q.order_hint && q.order_hint.why,
        ]),
      ]
        .filter(Boolean)
        .join("  ");
      for (const id of r.people) {
        push(QUOTE_TEXT, id, blob);
        push(NOTE_TEXT, id, notes);
      }
    }
  }
  const SCOPE_PLACEHOLDER = {
    names: "Search a name…",
    quotes: "Search quotes",
    all: "Search names, quotes, and info…",
  };
  function hitKind(p) {
    // "name" | "quote" | "note" | null
    if (!searchTerm) return null;
    if (
      searchScope !== "quotes" &&
      (NAME_TEXT.get(p.id) || "").includes(searchTerm)
    )
      return "name";
    if (
      searchScope !== "names" &&
      (QUOTE_TEXT.get(p.id) || "").includes(searchTerm)
    )
      return "quote";

    if (
      searchScope === "all" &&
      (NOTE_TEXT.get(p.id) || "").includes(searchTerm)
    )
      return "note";
    return null;
  }
  function updateSearchNote() {
    const el = $("#searchnote");
    if (!el) return;
    if (!searchTerm) {
      el.textContent = "";
      el.classList.remove("clickable");
      el.removeAttribute("role");
      el.removeAttribute("tabindex");
      el.removeAttribute("title");
      return;
    }

    const by = { name: 0, quote: 0, note: 0 };
    for (const p of WEB.people) {
      const k = hitKind(p);
      if (k) by[k]++;
    }
    const n = by.name + by.quote + by.note;
    if (!n) {
      el.textContent = "no match";
      el.classList.remove("clickable");
      el.removeAttribute("role");
      el.removeAttribute("tabindex");
      el.removeAttribute("title");
      return;
    }
    const people = `${n} ${n === 1 ? "person" : "people"}`;
    const parts = [
      by.name && `${by.name} by name`,
      by.quote && `${by.quote} in quotations`,
      by.note && `${by.note} in notes`,
    ].filter(Boolean);
    el.textContent =
      parts.length > 1
        ? `${people} — ${parts.join(", ")}`
        : by.name
          ? people
          : `${people}, matched ${by.quote ? "in quotations" : "in notes"}`;

    el.classList.add("clickable");
    el.setAttribute("role", "button");
    el.setAttribute("tabindex", "0");
    el.title = "Show these on the map";
  }
  function focusSearchHits() {
    if (!searchTerm) return;
    const hits = nodes.filter((n) => personMatches(n.p));
    if (hits.length) fitNodes(hits);
  }
  {
    const el = $("#searchnote");
    if (el) {
      el.addEventListener("click", focusSearchHits);
      el.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          focusSearchHits();
        }
      });
    }
  }

  function personHidden(p) {
    // dimmed by a legend switch
    return offGroups.has(p.group) || (p.gender && offGenders.has(p.gender));
  }

  function soloFromChip(g) {
    if (soloKey.group !== g && location.hash) location.hash = ""; // back out of the selection first
    toggleSolo("group", g);
  }
  function personMatches(p) {
    // survives the search box
    return !searchTerm || hitKind(p) !== null;
  }
  function applyFilters() {
    for (const e of edges) {
      e.g.classList.toggle("hidden", offCerts.has(e.r.certainty));
      const gdim = personHidden(e.a.p) || personHidden(e.b.p);
      const sdim = !(personMatches(e.a.p) || personMatches(e.b.p));
      e.g.classList.toggle("dimmed", searchTerm ? sdim : gdim);
    }
    for (const n of nodes) {
      const es = byPerson.get(n.id) || [];

      const allHidden = es.length
        ? es.every((r) => offCerts.has(r.certainty))
        : false;
      const dim = searchTerm ? !personMatches(n.p) : personHidden(n.p);
      n.g.classList.toggle("leadonly", allHidden && !dim);
      n.g.classList.toggle("dimmed", dim);
    }
  }
  $("#search").addEventListener("input", (ev) => {
    searchTerm = ev.target.value.trim().toLowerCase();
    applyFilters();
    updateSearchNote();
  });
  $("#searchscope").addEventListener("change", (ev) => {
    searchScope = ev.target.value;
    $("#search").placeholder = SCOPE_PLACEHOLDER[searchScope] || "Search…";
    applyFilters();
    updateSearchNote();
  });
  $("#search").addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      ev.target.value = "";
      searchTerm = "";
      applyFilters();
      updateSearchNote();
    }
    if (ev.key === "Enter" && searchTerm) {
      const named = WEB.people.filter((p) => hitKind(p) === "name");
      const any = WEB.people.filter((p) => hitKind(p) !== null);
      const pick =
        named.length === 1 ? named[0] : any.length === 1 ? any[0] : null;
      if (pick) location.hash = `#/p/${pick.id}`;
    }
  });

  const panel = $("#panel");
  function certBadge(r) {
    const SAMPLES = {
      "self-reported":
        '<line x1="1" y1="5" x2="27" y2="5" stroke="var(--edge)" stroke-width="2.9"/>',
      "second-hand":
        '<line x1="1" y1="5" x2="27" y2="5" stroke="var(--edge)" stroke-width="1.9" stroke-dasharray="7 5"/>',
      uncorroborated:
        '<line x1="1" y1="5" x2="27" y2="5" stroke="var(--edge)" stroke-width="1.8" stroke-dasharray="1.5 6" stroke-linecap="round"/>',
      married:
        '<line x1="1" y1="5" x2="27" y2="5" stroke="var(--edge)" stroke-width="5"/><line x1="1" y1="5" x2="27" y2="5" stroke="var(--paper)" stroke-width="1.8"/>',
      "attraction-expressed":
        '<line x1="1" y1="5" x2="21" y2="5" stroke="var(--edge)" stroke-width="1.7" stroke-dasharray="2 3 6 3"/><path d="M21,1.5 L27,5 L21,8.5 z" fill="var(--edge)"/>',
    };
    const dir =
      r.certainty === "attraction-expressed" &&
      r.direction &&
      P.get(r.direction)
        ? ` — ${esc(P.get(r.direction).name.split(" ").slice(-1)[0])} to ${esc(
            P.get(r.people.find((x) => x !== r.direction))
              .name.split(" ")
              .slice(-1)[0],
          )}, ${esc(OUTCOME_LABEL[r.outcome] || r.outcome || "")}`
        : "";
    const sample = SAMPLES[r.certainty];
    return `<span class="badge">${sample ? `<svg width="28" height="10" aria-hidden="true">${sample}</svg>` : ""}${esc(CERT_LABEL[r.certainty])}${dir}</span>`;
  }
  function miniBadge(c) {
    if (c === "attraction-expressed")
      return `<svg class="mini" width="24" height="8" aria-hidden="true"><line x1="1" y1="4" x2="17" y2="4" stroke="var(--edge)" stroke-width="1.6" stroke-dasharray="2 3 5 3"/><path d="M17,1 L22,4 L17,7 z" fill="var(--edge)"/></svg>`;
    if (c === "platonic")
      // platonic draws no line, so its marker is the word, not a sample
      return `<span class="mini-plat">platonic</span>`;
    return `<svg class="mini" width="32" height="8" aria-hidden="true">${SAMPLES[c]}</svg>`;
  }

  function byEvidenceDate(list, get) {
    const g = get || ((x) => x);
    const key = (x) => {
      const s = g(x),
        d = (s && s.evidence_date) || (s && s.order_hint);
      return d && d.y ? [d.y, d.m || 0, d.d || 0] : null;
    };
    return list
      .map((s, i) => [s, i])
      .sort((a, b) => {
        const ka = key(a[0]),
          kb = key(b[0]);
        if (ka && kb) {
          for (let i = 0; i < 3; i++) if (ka[i] !== kb[i]) return ka[i] - kb[i];
          return a[1] - b[1];
        }
        if (ka) return -1;
        if (kb) return 1;
        return a[1] - b[1];
      })
      .map((x) => x[0]);
  }

  const NAME_INDEX = (() => {
    const norm = (s) =>
      String(s || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .replace(/[.'’]/g, "")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
    const m = new Map();
    for (const p of WEB.people) {
      const keys = [p.name, p.sort_name, ...(p.aka || [])];
      if (p.sort_name && p.sort_name.includes(",")) {
        // "Doyle, Peter" -> "Peter Doyle"
        const [sur, rest] = p.sort_name.split(",");
        keys.push(`${rest.trim()} ${sur.trim()}`);
      }
      for (const k of keys) {
        const n = norm(k);
        if (!n) continue;
        if (m.has(n) && m.get(n) !== p.id) {
          m.set(n, null);
          continue;
        } // ambiguous: link neither
        if (!m.has(n)) m.set(n, p.id);
      }
    }
    return { norm, get: (s) => m.get(norm(s)) || null };
  })();

  function whenLabel(q) {
    const d = q && q.evidence_date;
    if (d && d.y != null) return fmtDate(d);
    return q && q.order_hint && q.order_hint.y ? "undated" : "";
  }

  function shortWho(s) {
    if (!s) return "";
    const main = String(s)
      .split(",")[0]
      .trim()
      .replace(/\s*\(.*\)$/, "");
    const w = main
      .split(/\s+/)
      .filter((x) => !/^(sir|mr|mrs|dr|lord|lady|the)\.?$/i.test(x));
    return w.length ? w[w.length - 1] : main;
  }

  const ABBREV =
    /\b(?:Mr|Mrs|Ms|Dr|St|Sir|Rev|Hon|Capt|Col|Lieut|Lt|Prof|Messrs|Jr|Sr|Esq|No|vol|pp?)\.$/;
  const ABBREV_ANY =
    /\b(?:Mr|Mrs|Ms|Dr|St|Sir|Rev|Hon|Capt|Col|Lieut|Lt|Prof|Messrs|Jr|Sr|Esq|No|vol|pp?)\./g;
  function splitQuestionTail(s) {
    const re = /[.!?…"'\]]\s+/g;
    let m,
      best = null;
    while ((m = re.exec(s))) {
      const head = s.slice(0, m.index + 1),
        tail = s.slice(m.index + m[0].length).trim();
      if (!/\?$/.test(tail)) continue; // the tail has to BE a question
      if (/[.!?]/.test(tail.slice(0, -1))) continue; // …and only one
      if (ABBREV.test(head.trim())) continue; // "Mr." ends a title, not a sentence
      best = { head: head.trim(), tail };
    }
    return best;
  }
  function parseExchange(q) {
    const raw = (q.quote || "").trim();
    if (!raw) return null;
    const turns = [];
    if (/\b[A-Z][A-Z .'-]*:/.test(raw)) {
      // explicitly labelled speakers
      const parts = raw
        .split(/\s*\b([A-Z][A-Z .'-]*[A-Z]):\s*/)
        .filter((s) => s !== "");
      if (parts.length < 2) return null;
      // an unlabelled preamble before the first name keeps its own row, unattributed
      let i = 0;
      if (!/^[A-Z][A-Z .'-]*[A-Z]$/.test(parts[0])) {
        turns.push({ who: "", text: parts[0] });
        i = 1;
      }
      for (; i + 1 < parts.length; i += 2) {
        const who = parts[i].charAt(0) + parts[i].slice(1).toLowerCase();
        turns.push({ who, text: parts[i + 1].trim() });
      }
      return turns.length > 1 ? turns : null;
    }
    const chunks = raw.split(/(?<=\?)\s*[—–]\s*/);
    if (chunks.length < 2) return null;
    const asks = shortWho(q.addressee) || "Q.",
      says = shortWho(q.speaker) || "A.";
    for (let i = 0; i < chunks.length; i++) {
      const c = chunks[i].trim();
      // Every chunk but the last ends on a question, and may carry the tail of the previous answer
      // in front of it - including the first, which opens mid-answer.
      const last = i === chunks.length - 1;
      const cut = last ? null : splitQuestionTail(c);
      if (cut) {
        if (cut.head) turns.push({ who: says, text: cut.head });
        turns.push({ who: asks, text: cut.tail });
      } else if (last) turns.push({ who: says, text: c });
      // One sentence, so the whole chunk IS the question. The abbreviation test matters here too:
      // "Did any impropriety take place between you and Mr. Wilde?" is one question, and reading the
      // stop in "Mr." as a sentence break left it unattributed.
      else if (!/[.!?…]\s+\S/.test(c.replace(ABBREV_ANY, "")))
        turns.push({ who: asks, text: c });
      else turns.push({ who: "", text: c });
    }
    return turns;
  }

  const LANG_NAME = {
    fr: "French",
    it: "Italian",
    de: "German",
    es: "Spanish",
    la: "Latin",
    el: "Greek",
    ru: "Russian",
    da: "Danish",
    nl: "Dutch",
    pt: "Portuguese",
  };
  function personLink(name) {
    const id = NAME_INDEX.get(name);
    return id
      ? `<a class="qlink" href="#/p/${esc(id)}">${esc(name)}</a>`
      : esc(name);
  }

  function withBar(withWhom, when) {
    if (!withWhom && !when) return "";

    // Each name and its line-sample travel as one unit: the pair is what identifies the
    // connection, and a wrap that leaves the chip stranded on the next line reads as though it
    // belongs to whoever follows.
    const one = (w) =>
      w && w.r
        ? `<span class="qpair"><a href="#/r/${esc(w.r.id)}">${esc(w.other.name)}</a>${miniBadge(w.r.certainty)}</span>`
        : w && w.label
          ? `<span class="qpair">${w.labelId ? `<a href="#/p/${esc(w.labelId)}">${esc(w.label)}</a>` : esc(w.label)}${w.owner && w.labelId && w.owner !== w.labelId ? `<a class="noedge" href="#/pair/${esc(w.owner)}--${esc(w.labelId)}" title="All sources connecting these two">no connection</a>` : `<span class="noedge">no connection</span>`}</span>`
          : "";

    // Dedupe by WHO, not by rendered html. One quotation can reach this card through two records
    // naming the same person - a stray duplicate engagement, say - and without this the header
    // reads "with George Alexander and George Alexander".
    const seen = new Set();
    const parts = [withWhom]
      .concat((withWhom && withWhom.also) || [])
      .filter((w) => {
        const key =
          w &&
          (w.r ? `r:${w.r.id}` : w.label ? `l:${w.labelId || w.label}` : "");
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .map(one)
      .filter(Boolean);
    const who = parts.length
      ? `with ${parts.join(' <span class="qand">and</span> ')}`
      : "";
    // Names and date are separate cells: the names column wraps, the date stays on one line at
    // the right rather than being carried down by a long list of names.
    return `<div class="qwith">${who ? `<span class="qnames">${who}</span>` : ""}${when ? `<span class="qdate">${esc(when)}</span>` : ""}</div>`;
  }
  // Every facsimile opened this session, indexed by the number its button carries. The reader is
  // one element reused by every card, so the card hands it a number rather than a copy of the
  // record - cards are rebuilt on every filter keystroke and would otherwise leak a page of
  // manifest data each time.
  const FACS = [];
  function facsButton(q) {
    const f = q && q.facsimile;
    if (!f || !f.pages || !f.pages.length) return "";
    const n = FACS.push(f) - 1;
    const arc = (WEB.archives || {})[f.archive] || {};
    const title = ((arc.items || {})[f.item] || {}).title || "Manuscript";
    const many = f.pages.length > 1;
    return `<button class="qfacs" data-facs="${n}" title="${esc(
      `${title} — ${f.pages.length} page${many ? "s" : ""} at full resolution`,
    )}"><svg class="qfacs-i" viewBox="0 0 16 16" aria-hidden="true" focusable="false"
      ><circle cx="6.8" cy="6.8" r="4.3" fill="none" stroke="currentColor" stroke-width="1.5"
      /><path d="M10 10 L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
      /></svg>View original</button>`;
  }
  // Which letters have a full text. The ids alone ride in the bundle - a few KB - so a card can
  // decide whether to draw the button without fetching a quarter of a megabyte of letters that
  // most readers never open. The text itself comes on the first click.
  let LETTERS = null;
  const hasLetter = (q) =>
    q && q.letter_id && (WEB.transcribed || []).includes(q.letter_id)
      ? q.letter_id
      : "";
  function letterButton(q) {
    const id = hasLetter(q);
    if (!id) return "";
    // Only worth pressing where the card shows less than the whole letter, which is the case it
    // exists for - but an unelided quotation is still an excerpt of a longer document, so the
    // button is offered either way and says which it is.
    const cut = q.verification === "verified-elision";
    return `<button class="qfacs qletter" data-letter="${esc(id)}" title="${esc(
      cut
        ? "This quotation is cut. Read the whole letter, with the quoted passage marked, and see what the ellipsis dropped."
        : "Read the whole letter, with the quoted passage marked.",
    )}"><svg class="qfacs-i" viewBox="0 0 16 16" aria-hidden="true" focusable="false"
      ><path d="M3 2.5h10v11H3z" fill="none" stroke="currentColor" stroke-width="1.4"
      /><path d="M5.2 5.5h5.6M5.2 8h5.6M5.2 10.5h3.2" stroke="currentColor" stroke-width="1.2"
      stroke-linecap="round"/></svg>${cut ? "Read the whole letter" : "Read in full"}</button>`;
  }
  function docChip(q) {
    const meta = DOC_META[q && q.document];
    if (!meta) return "";
    const [label, hand] = meta;
    // Offered on printed documents too. A copy carries what the printing does not - an
    // inscription, marginalia, a correction, a cancelled leaf - so going to it settles something
    // in either case; what it settles is what differs. `hand` picks the wording, not the tick.
    const seen = q.verified_against_original === true;
    const l = label.toLowerCase();
    const what = seen
      ? hand
        ? `The ${l} itself has been read — in the original hand, not only in print.`
        : `The ${l} itself has been read, not only the edition quoted here.`
      : hand
        ? `Quoted from a ${l}, read in print. The original has not been checked.`
        : `Quoted from a ${l}. The copy itself has not been checked for anything the printing does not carry.`;
    // A button, not a label: clicking narrows the panel to this kind of document, which is the
    // question the chip provokes ("how much of this rests on letters?") answered in one click.
    return `<button class="chip doc${seen ? " seen" : ""}" data-doc="${esc(q.document)}"
      aria-pressed="false" title="${esc(what + " Click to show only these.")}"
      >${seen ? "✓ " : ""}${esc(label)}</button>`;
  }
  function chipRow(q, vLabel, vClass) {
    // Where there is no scan, the archive holding the original is still worth saying: it is the
    // difference between a document we cannot show and a document nobody can find.
    const ms = q && q.manuscript;
    // Where the document is. The chip prints the ABBREVIATION - "Clark, UCLA" for the forty-four
    // characters of "William Andrews Clark Memorial Library, UCLA" - and the full name is on
    // hover, where a name that long can be read without crowding the card.
    const loc = q && q.location;
    // EVERY location here is a LAST KNOWN location, institutions included. Nothing on this map
    // has been confirmed by going to an archive; each one is what an edition recorded, and
    // editions have dates. The Complete Letters say as much of private hands on p. xviii - "the
    // last known location" - and the Hyde Collection proves it of institutions too, having
    // become the British Library since the volume named it. So the chip names its authority and
    // its year rather than asserting a present tense it cannot support.
    // WHO placed the document there. Not the work's author: Wilde did not record where his own
    // manuscripts are, his editors did, and `short_cite` names the author because it is built to
    // cite the TEXT. A collected edition's headnotes belong to whoever edited it. And where the
    // location came from a different book than the quotation — three Ricketts letters quoted
    // from Self-Portrait, which names no locations, and placed by Delaney's biography — the
    // record says so itself in `recorded_by`.
    const wk = q && WEB.works[q.work];
    const eds =
      wk && wk.editors
        ? wk.editors
            .split(";")[0]
            .replace(/\s*\([^)]*\)/g, "")
            .trim()
        : "";
    const by =
      (loc && loc.recorded_by) ||
      (eds && wk ? `${eds}, in ${wk.short_cite}` : "") ||
      (wk ? wk.short_cite : "");
    const said = by ? `Last recorded by ${by}` : "Last recorded";
    // Four of the locations are not institutions, and each needs its own sentence: "survives at
    // Published work" would read as a place with a name. Three of them answer the question
    // without naming anywhere at all, which is the point of them - a reader wants to know
    // whether they can go and read the thing, and "no archive recorded" never said.
    const SAID = {
      "Private collection":
        `${said} as belonging to ${loc && loc.owner ? loc.owner : "a private owner it does not name"}` +
        ". Private collections are dispersed and sold without notice, so this is where the " +
        "document was, not a claim about where it is.",
      "Private inbox":
        "Written to the citing author directly and never published. Nothing about it is " +
        "unknown; there is simply nowhere a reader can go and read it.",
      "Published work":
        "The document is the published work itself, so there is no single original to see. " +
        "Any library that holds the edition holds it.",
      "Published on the web":
        "Published online and read where it is published. No library holds a copy, and it can " +
        "be changed or taken down by whoever put it up.",
      "Location unknown":
        "Nobody has traced the original. Usually it is a letter the editors could only print " +
        "from a memoir or an auction catalogue — which may mean the sheet still exists in " +
        "somebody's hands, and may mean it is gone. Neither is recorded, and that is the point.",
    };
    // `archived_as` is present only where what the archive holds is not what the document type implies:
    // a letter surviving as somebody else's typescript. That is worth saying on the chip,
    // because a typescript cannot settle emphasis - whoever typed it already decided what the
    // underlining meant - and settling emphasis is what naming a repository is for.
    // `as_of` replaces the citing edition's date, for a holding last attested long before the
    // book that reports it — a letter last seen in a saleroom in 1927 and printed from the sale
    // catalogue by editors writing in 2000, who never saw it either.
    const held =
      loc && loc.as_of
        ? `Last known at ${loc.full}, ${loc.as_of}. Nothing has been recorded of it since, and ` +
          `whoever took it home is not named.`
        : loc && loc.archived_as === "typescript"
          ? `${said} as a TYPESCRIPT at ${loc.full} — not the document itself, and not a witness ` +
            `to its emphasis, since whoever typed it had already read the underlining for you.`
          : loc && loc.archived_as === "autograph"
            ? `${said} as surviving in manuscript at ${loc.full}, though its kind would not lead ` +
              `you to expect that.`
            : ms
              ? `${said} at ${loc.full}. This map does not hold a scan of it, and has not ` +
                `confirmed the holding since.`
              : // The one location that is NOT a last-known claim. A facsimile draws the archive's
                // own image service live, so the page you are looking at is proof the archive has
                // it today - there is nothing stale to warn about.
                `Held at ${loc.full}, which serves the scan this map shows.`;
    const msChip = loc
      ? `<button class="chip loc" data-loc="${esc(loc.short)}" aria-pressed="false" title="${esc(
          (SAID[loc.full] || held) + " Click to show only these.",
        )}">${
          ms && ms.url
            ? `<a href="${esc(ms.url)}" target="_blank" rel="noopener">${esc(loc.short)}</a>`
            : esc(loc.short)
        }</button>`
      : "";
    const bits = [
      docChip(q),
      vLabel ? `<span class="chip ${vClass}">${vLabel}</span>` : "",
      letterButton(q),
      facsButton(q),
      msChip,
    ].filter(Boolean);
    return bits.length ? `<div class="chips">${bits.join("")}</div>` : "";
  }
  function quoteCard(q, withWhom, si) {
    const [vLabel, vClass] =
      VER_META[q.verification || "unverified"] || VER_META.unverified;
    const siAttr = si == null ? "" : ` data-si="${si}"`; // the handle the sources filter hides the card by
    const wk = WEB.works[q.work] || null;

    const byline = wk
      ? q.speaker ||
        (q.voice === "modern" && wk.editors
          ? `${wk.editors}, eds.`
          : wk.author || "")
      : "";
    const inVol = wk && byline && byline !== (wk.author || "") ? ", in " : ", ";

    const bcut = byline.indexOf(","); // NOT `cut` - the speaker heading below already owns that name
    const bylineHtml = byline
      ? personLink(bcut > 0 ? byline.slice(0, bcut) : byline) +
        (bcut > 0 ? esc(byline.slice(bcut)) : "")
      : "";
    const attr = wk
      ? `— ${bylineHtml}${byline ? inVol : ""}<i>${esc(wk.title || q.work)}</i>${wk.year ? ` (${wk.year})` : ""}${q.locator ? `, ${esc(q.locator)}` : ""}.`
      : q.locator
        ? `— ${esc(q.locator)}.`
        : "";
    const prov = (q.citation_provenance || "").trim();
    if ((q.quote || "") === "") {
      return `<div class="qcard qpointer"${siAttr}>
      ${withBar(withWhom, whenLabel(q))}
      <div class="qhead">Source pointer — not yet transcribed</div>
      ${q.supports ? `<div class="qclaim">${esc(q.supports)}</div>` : ""}
      <div class="qattr">${attr || (wk ? "" : "Source to be confirmed.")}</div>
      <div class="chips"><span class="chip v-pend">⧖ Pending verification</span></div>
    </div>`;
    }

    const auth = (wk && wk.author) || "";
    const authIsEditor = /,\s*eds?\.?$/i.test(auth.trim());

    const spk =
      q.voice === "period" ? q.speaker || (authIsEditor ? "" : auth) || "" : "";
    const cut = spk.indexOf(",");
    let spkMain = cut > 0 ? spk.slice(0, cut) : spk,
      spkRest = cut > 0 ? spk.slice(cut + 1).trim() : "";

    const to = q.addressee || "";
    const when = whenLabel(q);
    if (
      to &&
      /^(letter|note|telegram|postcard|diary|memoir)?\s*to\s+/i.test(spkRest)
    )
      spkRest = "";
    return `<div class="qcard"${siAttr}>
    ${withBar(withWhom, when)}
    ${q.context ? `<div class="qctx${q.context.length > 90 ? " long" : ""}">${fmtEmphasis(esc(q.context))}</div>` : ""}
    ${spk ? `<div class="qspeaker">${personLink(spkMain)}${spkRest ? `<span class="qspeaker-x">, ${esc(spkRest)}</span>` : ""}${to ? `<span class="qspeaker-to"> to </span>${personLink(to)}` : ""}</div>` : ""}
    ${(() => {
      const langAttr = q.lang ? ` lang="${esc(q.lang)}"` : "";
      if (q.voice === "court") {
        const turns = q.turns && q.turns.length ? q.turns : null;

        if (turns)
          return `<blockquote class="q-court"${langAttr}>${turns
            .map(
              (t) =>
                `<span class="who">${esc(t.who || "")}</span><span class="said">${fmtEmphasis(esc(t.text))}</span>`,
            )
            .join("")}</blockquote>`;
        // No transcript, but still a court record with someone speaking - a plea is filed BY
        // somebody. Label it the way a turn is labelled, so a plea and a cross-examination carry
        // their speaker in the same place and the same type. Only the name: the capacity after
        // the comma ("plea of justification, filed 30 March 1895") is what `context` is for, and
        // it would not survive being set in a 12px uppercase label.
        const who = (q.speaker || "").split(",")[0].trim();
        return `<blockquote class="q-court plain"${langAttr}>${
          who ? `<span class="who">${esc(who)}</span>` : ""
        }<span class="said">${fmtEmphasis(esc(q.quote))}</span></blockquote>`;
      }
      return `<blockquote class="${q.voice === "period" ? "q-period" : "q-modern"}"${langAttr}>${fmtEmphasis(esc(q.quote))}</blockquote>`;
    })()}
    ${q.translation ? `<div class="qtrans"><span class="qtrans-h">${esc(LANG_NAME[q.lang] || q.lang)} ⟶ English</span>${fmtEmphasis(esc(q.translation))}${q.translation_note ? `<span class="qtrans-n">${esc(q.translation_note)}</span>` : ""}</div>` : ""}
    <div class="qattr">${attr}</div>
    ${q.supports ? `<div class="qsupports">Support: ${esc(q.supports)}</div>` : ""}
    ${q.order_hint && q.order_hint.why ? `<div class="qplaced">Undated — placed here for reading order: ${esc(q.order_hint.why)}</div>` : ""}
    ${chipRow(q, vLabel, vClass)}
    ${
      prov
        ? `<details><summary>Provenance</summary><div>${esc(prov)}${howLabel(q.how_verified) ? ` · ${esc(howLabel(q.how_verified))}` : ""}${q.verified_on ? ` · ${esc(q.verified_on)}` : ""}${
            // The document gets its own paragraph, because it answers a different question from the
            // reprinting above it and reading them as one sentence is what let a PDF page number pass
            // for a manuscript. `marks_verified` closes it: the marks were collated and they match.
            (q.original_provenance || "").trim()
              ? `<p class="qorig"><b>At the document.</b> ${esc(q.original_provenance)}${
                  q.marks_verified
                    ? ` <span class="qmarks">Emphasis, accents and punctuation collated against it; this quotation matches.</span>`
                    : ""
                }</p>`
              : ""
          }</div></details>`
        : ""
    }
  </div>`;
  }

  const SRC_FILTER_MIN = 1;
  // What is HIDDEN, so that empty means everything shows and the checkboxes can be checked by
  // default without lying about the panel. Named for the legend's `offGroups`, which works the
  // same way and for the same reason.
  // Two facets, one implementation. Each keeps what is HIDDEN, so empty means everything shows
  // and the boxes can be checked by default without lying about the panel.
  // Three of the location facet's members are not places. They are what "where is this" comes
  // to for a published book, a page on the web, and a document nobody has traced, and they sort
  // below every archive however many of them there are - for the same reason the blank does,
  // being the residue rather than a rival. Built in tools/validate.py, DERIVED_LOCATION.
  const DERIVED_LOC = ["Published", "Online", "Unknown"];
  const rank = (k) => (k === "" ? 2 : 0);
  const FACETS = {
    doc: {
      off: new Set(),
      solo: null,
      prev: new Set(),
      attr: "doc",
      resting: "Type",
      rank,
      label: (k) => (k ? (DOC_META[k] || [])[2] || k : "Not recorded"),
    },
    loc: {
      off: new Set(),
      solo: null,
      prev: new Set(),
      attr: "loc",
      resting: "Location",
      rank: (k) => (k === "" ? 2 : DERIVED_LOC.includes(k) ? 1 : 0),
      label: (k) => k || "Not recorded",
    },
  };
  // Show only this kind; do it again to put back exactly what was hidden before, rather than
  // merely showing everything. Called by a chip on a card and by right-clicking a row of the
  // dropdown, which is the gesture the legend already teaches for its spheres and genders.
  function facetRows(a, root) {
    return [
      ...(root || document).querySelectorAll(
        `#sffilter .sfdocopt[data-facet="${a.attr}"] input[type=checkbox]`,
      ),
    ];
  }
  function facetKinds(a) {
    // The All row has no `value`; it would land in the set as "on".
    return facetRows(a)
      .filter((b) => !b.dataset.all)
      .map((b) => b.value);
  }
  function soloFacet(a, k) {
    if (a.solo === k) {
      a.off = new Set(a.prev);
      a.solo = null;
      return;
    }
    if (a.solo === null) a.prev = new Set(a.off);
    a.off = new Set(facetKinds(a).filter((v) => v !== k));
    a.solo = k;
  }
  let reapplySrcFilter = null;

  const MARK_MIN = 2;
  let PANEL_SRC = []; // {hay,y,doc,loc,q} per rendered card, indexed by its data-si
  function srcYear(q) {
    const d =
      q && q.evidence_date && q.evidence_date.y != null
        ? q.evidence_date
        : q && q.order_hint && q.order_hint.y != null
          ? q.order_hint
          : null;
    return d ? d.y : null;
  }

  // Three haystacks per source, so the filter's scope selector narrows the same way the
  // header search does.
  function srcHay(q, withWhom) {
    const wk = WEB.works[q.work] || null;
    const join = (a) => a.filter(Boolean).join("  ").toLowerCase();
    // Every name the card's header can show, including the ones folded into `also`. One quotation
    // can reach a panel through several records and merge into a single card, so the haystack has
    // to hold every merged name, not just the primary.
    const partner = (w) =>
      w && ((w.other && w.other.name) || w.label || (w.r && w.r.id));
    const names = join([
      q.speaker,
      q.addressee,
      wk && wk.author,
      wk && wk.editors,
      partner(withWhom),
      ...((withWhom && withWhom.also) || []).map(partner),
      ...(q.turns || []).map((t) => t.who),
    ]);
    const quotes = join([
      q.quote,
      q.translation,
      q.translation_note,
      ...(q.turns || []).map((t) => t.text),
    ]);
    return { names, quotes, all: srcHayAll(q, withWhom, wk) };
  }

  function srcHayAll(q, withWhom, wk) {
    return [
      q.quote,
      q.translation,
      q.translation_note,
      q.context,
      q.speaker,
      q.addressee,
      q.supports,
      q.locator,
      q.citation_provenance,
      q.how_verified,
      wk && wk.title,
      wk && wk.author,
      wk && wk.editors,
      wk && wk.year,
      withWhom && withWhom.other && withWhom.other.name,
      q.order_hint && q.order_hint.why,
      ...(q.turns || []).flatMap((t) => [t.who, t.text]),
    ]
      .filter(Boolean)
      .join("  ")
      .toLowerCase();
  }

  function sourceFilterBar(n) {
    if (n < SRC_FILTER_MIN) return "";
    const ys = PANEL_SRC.map((s) => s.y).filter((y) => y != null);
    const lo = ys.length ? Math.min(...ys) : "",
      hi = ys.length ? Math.max(...ys) : "";
    // "" is a real member, not an absence to be skipped. Without it a solo cannot hide the
    // sources that never said where the document is, and soloing Magdalen showed 190 cards
    // instead of 13 - the thirteen plus everyone who had answered no question at all.
    const docs = new Map();
    for (const r of PANEL_SRC)
      docs.set(r.doc || "", (docs.get(r.doc || "") || 0) + 1);
    const locs = new Map();
    for (const r of PANEL_SRC)
      locs.set(r.loc || "", (locs.get(r.loc || "") || 0) + 1);

    // Both dropdowns are the same control over a different question, so they are the same
    // markup. Ordered by how many of each the panel holds, which puts the label on the kind that
    // dominates a selection and the commonest choice under the cursor.
    // One group per facet inside a single box. The label function comes from FACETS and is the
    // same one the sync and the summary use, so an option, a pressed chip and a collapsed label
    // can never name the same key three different ways.
    const facetGroup = (a, counts, allLabel) => {
      const label = a.label;
      const opts = [...counts]
        // The residue goes last however much of it there is: the blank, and for locations the
        // three answers that are not archives.
        .sort(
          (b, c) =>
            a.rank(b[0]) - a.rank(c[0]) ||
            c[1] - b[1] ||
            label(b[0]).localeCompare(label(c[0])),
        )
        .map(
          ([k, c]) =>
            `<label class="sfdocopt" data-facet="${a.attr}" title="${esc(
              `${label(k)} · ${c} · right-click to show only this`,
            )}"><input type="checkbox" value="${esc(k)}" checked>` +
            `<span>${esc(label(k))}</span><b>${c}</b></label>`,
        )
        .join("");
      const total = [...counts.values()].reduce((x, y) => x + y, 0);
      return `<label class="sfdocopt sfdocall" data-facet="${a.attr}"
        title="Show every ${esc(a.resting.toLowerCase())} again"
        ><input type="checkbox" data-all="1" checked><span>${esc(allLabel)}</span
        ><b>${total}</b></label>${opts}`;
    };
    const docSel = `<details id="sffilter" class="sfdoc"${
      docs.size || locs.size ? "" : " data-empty"
    }>
        <summary aria-label="Filter by kind of document and where it is held"
          ><span class="sfdocsum">Type &amp; location</span></summary>
        <div class="sfdocbox">
          <div role="group" aria-label="Kind of document">${facetGroup(
            FACETS.doc,
            docs,
            "All types",
          )}</div>
          <div role="group" aria-label="Where the document is held" class="sfdocgroup">${facetGroup(
            FACETS.loc,
            locs,
            "All locations",
          )}</div>
        </div>
      </details>`;
    return `<div class="sfilter">
    <div class="sfqwrap">
      <div class="sfqfield">
        <input id="sfq" class="sfq" type="search" autocomplete="off" spellcheck="false"
               placeholder="Search sources…" aria-label="Search sources">
        <span id="sfcount" class="sfcount" role="status"></span>
      </div>
      <select id="sfscope" class="sfscope" aria-label="What to filter on">
        <option value="all" selected>All</option>
        <option value="names">Names</option>
        <option value="quotes">Quotes</option>
      </select>
    </div>
    <div class="sfrow">
      <label class="sfyl" for="sfy1">Years</label>
      <input id="sfy1" class="sfy" inputmode="numeric" maxlength="4" placeholder="${lo}" aria-label="From year">
      <span class="sfdash">–</span>
      <input id="sfy2" class="sfy" inputmode="numeric" maxlength="4" placeholder="${hi}" aria-label="To year">
      <button id="sfclear" class="sfclear" type="button" aria-label="Clear year range" hidden>Clear</button>
      ${docSel}
    </div>
  </div>
  <p id="sfnone" class="sfnone" hidden>Nothing here matches. The filter reads the quotation, its
     translation, the speaker, the work and the provenance notes — not only the words in the quote.</p>`;
  }

  let titleWatch = null;
  function wirePanelTitle() {
    if (titleWatch) {
      titleWatch.disconnect();
      titleWatch = null;
    }
    const slot = panel.querySelector(".phead .phtitle"),
      h2 = panel.querySelector(".pwrap>h2");
    if (!slot || !h2) return;

    slot.innerHTML = h2.innerHTML.trim();
    const head = panel.querySelector(".phead");
    titleWatch = new IntersectionObserver(
      ([e]) => slot.classList.toggle("show", !e.isIntersecting),
      {
        root: panel,
        rootMargin: `-${Math.round(head.getBoundingClientRect().height)}px 0px 0px 0px`,
        threshold: 0,
      },
    );
    titleWatch.observe(h2);
  }

  function wirePanelHandle() {
    const h = panel.querySelector(".phead .grab");
    if (!h) return;
    let start = null;
    const settle = (ms) =>
      setTimeout(() => {
        panel.style.transition = "";
      }, ms);
    h.addEventListener("pointerdown", (e) => {
      start = { y: e.clientY, t: performance.now() };
      h.setPointerCapture(e.pointerId);
      panel.style.transition = "none";
    });
    h.addEventListener("pointermove", (e) => {
      if (!start) return;
      panel.style.transform = `translateY(${Math.max(0, e.clientY - start.y)}px)`;
    });
    const end = (e) => {
      if (!start) return;
      const dy = Math.max(0, e.clientY - start.y);

      const flick = dy / Math.max(1, performance.now() - start.t) > 0.5;
      start = null;
      panel.style.transition = "transform .18s ease-out";
      if (dy > 110 || (flick && dy > 24)) {
        panel.style.transform = "translateY(100%)";
        setTimeout(() => {
          panel.style.transition = "";
          panel.style.transform = "";
          location.hash = "";
        }, 170);
      } else {
        panel.style.transform = ""; // not far enough: spring back
        settle(200);
      }
    };
    h.addEventListener("pointerup", end);
    h.addEventListener("pointercancel", end);
  }

  const MARK_STOP = new Set(["SCRIPT", "STYLE", "MARK"]);
  function clearMarks(root) {
    const marks = root.querySelectorAll("mark.sfhit");
    if (!marks.length) return;
    for (const m of marks)
      m.replaceWith(document.createTextNode(m.textContent));
    root.normalize(); // rejoin the split halves, or repeated typing shreds the text nodes
  }
  function markTerm(root, term) {
    const low = term.toLowerCase();
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) =>
        MARK_STOP.has(n.parentNode.nodeName)
          ? NodeFilter.FILTER_REJECT
          : n.nodeValue.toLowerCase().includes(low)
            ? NodeFilter.FILTER_ACCEPT
            : NodeFilter.FILTER_SKIP,
    });
    const hits = [];
    while (walk.nextNode()) hits.push(walk.currentNode);
    let n = 0;
    for (const node of hits) {
      const s = node.nodeValue,
        frag = document.createDocumentFragment();
      let i = 0,
        j;
      while ((j = s.toLowerCase().indexOf(low, i)) >= 0) {
        if (j > i) frag.appendChild(document.createTextNode(s.slice(i, j)));
        const m = document.createElement("mark");
        m.className = "sfhit";
        m.textContent = s.slice(j, j + low.length);
        frag.appendChild(m);
        n++;
        i = j + low.length;
      }
      if (i < s.length) frag.appendChild(document.createTextNode(s.slice(i)));
      node.replaceWith(frag);
    }
    return n;
  }

  function flagHiddenHits(card) {
    const det = card.querySelector("details");
    if (det && !det.open && det.querySelector("mark.sfhit"))
      det.classList.add("sfdeep");
  }

  function wireSourceFilter() {
    for (const a of Object.values(FACETS)) {
      a.off = new Set();
      a.solo = null;
      a.prev = new Set();
    }
    reapplySrcFilter = null;
    const box = $("#sfq");
    if (!box) return;
    const scope = $("#sfscope") || { value: "all" };
    const y1 = $("#sfy1"),
      y2 = $("#sfy2"),
      cnt = $("#sfcount"),
      clr = $("#sfclear"),
      dsel = $("#sffilter"),
      none = $("#sfnone");
    const cards = [...panel.querySelectorAll(".qcard[data-si]")];
    const apply = () => {
      const term = box.value.trim().toLowerCase();
      const a = parseInt(y1.value, 10),
        b = parseInt(y2.value, 10);
      let lo = Number.isFinite(a) ? a : null,
        hi = Number.isFinite(b) ? b : null;
      if (lo != null && hi != null && lo > hi) [lo, hi] = [hi, lo]; // typed backwards: read it as a range anyway
      const dated = lo != null || hi != null;
      let shown = 0,
        dropped = 0;
      for (const el of cards) {
        const s = PANEL_SRC[+el.dataset.si] || { hay: {}, y: null };
        const hay = (s.hay && (s.hay[scope.value] ?? s.hay.all)) || "";
        let ok = !term || hay.includes(term);
        if (ok && FACETS.doc.off.size) ok = !FACETS.doc.off.has(s.doc || "");
        if (ok && FACETS.loc.off.size) ok = !FACETS.loc.off.has(s.loc || "");
        if (ok && dated) {
          if (s.y == null) {
            ok = false;
            dropped++;
          } else ok = (lo == null || s.y >= lo) && (hi == null || s.y <= hi);
        }
        el.classList.toggle("sfhide", !ok);
        if (ok) shown++;

        clearMarks(el);
        el.querySelectorAll("details.sfdeep").forEach((d) =>
          d.classList.remove("sfdeep"),
        );
        if (ok && term.length >= MARK_MIN) {
          markTerm(el, term);
          flagHiddenHits(el);
        }
      }
      const active =
        !!term || dated || FACETS.doc.off.size > 0 || FACETS.loc.off.size > 0;
      cnt.textContent = active
        ? `${shown} of ${cards.length}${dropped ? ` · ${dropped} undated hidden` : ""}`
        : "";
      cnt.parentElement.classList.toggle("counting", !!cnt.textContent);
      // Pressed means SOLOED. Marking every shown kind as pressed would light up almost every
      // chip on the panel and say nothing.
      for (const b of panel.querySelectorAll(".chip.doc[data-doc]")) {
        const soloed = FACETS.doc.solo === b.dataset.doc;
        b.setAttribute("aria-pressed", String(soloed));
        b.title =
          b.title.replace(
            / (?:Click to show only these\.|Showing only these — click to bring the rest back\.)$/,
            "",
          ) +
          (soloed
            ? " Showing only these — click to bring the rest back."
            : " Click to show only these.");
      }
      for (const b of panel.querySelectorAll(".chip.loc[data-loc]"))
        b.setAttribute(
          "aria-pressed",
          String(FACETS.loc.solo === b.dataset.loc),
        );
      // Each group keeps its own boxes and its own All; the collapsed label is the two
      // half-answers joined, because one control now stands for two questions.
      const syncFacet = (a) => {
        const rows = facetRows(a, dsel);
        if (!rows.length) return "";
        for (const cb of rows)
          if (!cb.dataset.all) cb.checked = !a.off.has(cb.value);
        const allBox = rows.find((cb) => cb.dataset.all);
        if (allBox) {
          const kinds = rows.length - 1;
          allBox.checked = a.off.size === 0;
          // Neither on nor off, and the honest picture of a partial selection: a bare unticked
          // box here would read as "nothing is shown", which is a different thing entirely.
          allBox.indeterminate = a.off.size > 0 && a.off.size < kinds;
        }
        // In the checkboxes' own order, which is by how many of each the panel holds - so the
        // label names the kind that dominates the selection rather than whichever sorts first.
        // Alphabetical put "Diaries +2" on a set of 251 letters and one diary.
        const picked = rows
          .filter((cb) => cb.checked && !cb.dataset.all)
          .map((cb) => a.label(cb.value));
        // Say whichever edit was the smaller one. Having hidden two of sixteen kinds, "Letters
        // +13" is accurate and tells you nothing; what you did was exclude two, so the label
        // says so. Narrow the other way and it names what is left instead.
        return !a.off.size
          ? ""
          : !picked.length
            ? "Nothing shown"
            : picked.length === 1
              ? picked[0]
              : a.off.size <= picked.length
                ? `All but ${a.off.size}`
                : `${picked[0]} +${picked.length - 1}`;
      };
      if (dsel) {
        const halves = [syncFacet(FACETS.doc), syncFacet(FACETS.loc)].filter(
          Boolean,
        );
        dsel.classList.toggle("on", halves.length > 0);
        dsel.querySelector(".sfdocsum").textContent = halves.length
          ? halves.join(" · ")
          : "Type & location";
      }

      clr.hidden = !dated;
      none.hidden = !(active && shown === 0);
    };
    reapplySrcFilter = apply;
    // Both dropdowns behave identically, so they are wired identically. (The braces matter: the
    // guard used to cover only the first listener, and the second would have thrown on a panel
    // that drew no dropdown at all.)
    // One box, so one pair of listeners; the row says which group it belongs to.
    const facetOf = (el) =>
      FACETS[(el.closest(".sfdocopt") || {}).dataset?.facet];
    const wireFacet = (el) => {
      if (!el) return;
      // Right-click a row to solo it, as in the legend. The label wraps the checkbox, so the
      // event has to be stopped before the browser's own menu and before the label forwards the
      // click on to the input and toggles it.
      el.addEventListener("contextmenu", (ev) => {
        const row = ev.target.closest && ev.target.closest(".sfdocopt");
        if (!row) return;
        ev.preventDefault();
        const cb = row.querySelector("input[type=checkbox]");
        const a = FACETS[row.dataset.facet];
        if (!cb || !a || cb.dataset.all) return;
        soloFacet(a, cb.value);
        apply();
      });
      el.addEventListener("change", (ev) => {
        const cb = ev.target;
        if (!cb || cb.type !== "checkbox") return;
        const a = facetOf(cb);
        if (!a) return;
        if (cb.dataset.all) {
          // Ticking it shows everything; unticking a fully ticked box hides everything. Reached
          // from indeterminate, either way round, the useful answer is "show me all of it".
          a.off = cb.checked ? new Set() : new Set(facetKinds(a));
          a.solo = null;
          apply();
          return;
        }
        // Clicking the row that is currently soloed lets go of the solo, exactly as clicking a
        // soloed legend row does. Without this the box simply unticks the one kind still
        // showing, hiding everything - the state the summary calls "Nothing shown".
        if (a.solo === cb.value) {
          soloFacet(a, cb.value); // same key toggles it off, restoring what was hidden before
          apply();
          return;
        }
        if (cb.checked) a.off.delete(cb.value);
        else a.off.add(cb.value);
        a.solo = null; // touching any other switch by hand ends the solo
        apply();
      });
    };
    wireFacet(dsel);
    box.addEventListener("input", apply);
    if (scope.addEventListener) scope.addEventListener("change", apply);
    y1.addEventListener("input", apply);
    y2.addEventListener("input", apply);
    clr.addEventListener("click", () => {
      y1.value = "";
      y2.value = "";
      apply();
      y1.focus();
    });

    box.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && box.value) {
        e.stopPropagation();
        box.value = "";
        apply();
      }
    });
    for (const el of [y1, y2])
      el.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && (y1.value || y2.value)) {
          e.stopPropagation();
          y1.value = "";
          y2.value = "";
          apply();
        }
      });
  }

  const SX_BY_PARTNER = (() => {
    const m = new Map();
    for (const p of WEB.people)
      for (const ce of p.sexuality_sources || []) {
        if (!(ce.sources || []).length) continue;
        const other = NAME_INDEX.get(ce.subject || "");
        if (!other || other === p.id) continue;
        if (!m.has(other)) m.set(other, []);
        m.get(other).push({ owner: p, ce });
      }
    return m;
  })();
  function sourcesByPerson(id) {
    const rels = (byPerson.get(id) || []).filter(
      (r) => (r.sources || []).length,
    );
    const flat = [];
    for (const r of rels) {
      const other = P.get(partnerOf(r, id));
      for (const q of r.sources || []) flat.push({ q, r, other });
    }

    const p2 = P.get(id);
    for (const ce of (p2 && p2.sexuality_sources) || []) {
      const other = NAME_INDEX.get(ce.subject || "");
      for (const q of ce.sources || [])
        flat.push({
          q,
          label: ce.subject || ce.name || "",
          labelId: other && other !== id ? other : null,
          owner: id,
        });
    }

    for (const { owner: ceOwner, ce } of SX_BY_PARTNER.get(id) || []) {
      for (const q of ce.sources || [])
        flat.push({ q, label: ceOwner.name, labelId: ceOwner.id, owner: id });
    }
    if (!flat.length) return "";

    const merged = [],
      byKey = new Map();
    for (const f of flat) {
      const txt = (f.q.quote || "").replace(/\W+/g, " ").trim().toLowerCase();
      if (!txt) {
        merged.push(f);
        continue;
      }
      const key = `${f.q.work}|${f.q.locator}|${txt}`;
      const first = byKey.get(key);
      if (first) {
        (first.also = first.also || []).push(f);
      } else {
        byKey.set(key, f);
        merged.push(f);
      }
    }
    PANEL_SRC = [];
    const cards = byEvidenceDate(merged, (f) => f.q)
      .map((f) => {
        PANEL_SRC.push({
          hay: srcHay(f.q, f),
          y: srcYear(f.q),
          doc: f.q.document || null,
          loc: (f.q.location || {}).short || null,
          q: f.q,
        });
        return quoteCard(f.q, f, PANEL_SRC.length - 1);
      })
      .join("");
    return (
      `<div class="sect">Sources, in chronological order (${merged.length})</div>` +
      `<p class="sect-note">Every quotation attached to this person, in the order the evidence was
       made${(() => {
         const c = rels.length,
           e = flat.some((f) => f.label);
         const conn =
           c === 1 ? "their one connection" : `all ${c} of their connections`;
         if (c && e)
           return `, from ${conn} and from sexuality sources not tied to a connection`;
         if (c) return `, from ${conn}`;
         return ", from sexuality sources not tied to a connection";
       })()}. Each says what it belongs to.</p>` +
      sourceFilterBar(merged.length) +
      cards
    );
  }
  function openPerson(id) {
    const p = P.get(id);
    if (!p) {
      closePanel();
      return;
    }
    const rels = byPerson.get(id) || [];
    const rows = [];
    if (p.born)
      rows.push({
        k: sortKey(p.born),
        cls: "anchor",
        when: fmtDate(p.born),
        what: "Born",
      });
    for (const r of rels) {
      const q = P.get(partnerOf(r, id));
      rows.push({
        k: sortKey(r.start),
        cls: "",
        when: relDateLabel(r),
        what: `<a href="#/r/${esc(r.id)}">${esc(q.name)}</a>${miniBadge(r.certainty)}`,
      });
    }
    for (const ce of p.sexuality_sources || []) {
      const otherId = NAME_INDEX.get(ce.subject || "");
      const ro = otherId && otherId !== p.id ? otherId : null;
      rows.push({
        k: sortKey(ce.start),
        cls: "sx",
        when:
          ce.start || ce.end
            ? `${fmtDate(ce.start)}${ce.end && ce.end.y != null ? ` – ${fmtDate(ce.end)}` : ""}`
            : "date unknown",
        what: `${ro ? `<a href="#/pair/${esc(p.id)}--${esc(ro)}">${esc(ce.subject)}</a>` : esc(ce.subject || ce.name || "unnamed")}${ro ? "" : `<span class="offr">off-roster</span>`}${ce.note ? `<div style="font-size:12px;color:var(--ink3)">${esc(ce.note)}</div>` : ""}`,
      });
    }
    rows.sort((a, b) => (a.k === Infinity) - (b.k === Infinity) || a.k - b.k);
    if (p.died)
      rows.push({
        k: sortKey(p.died),
        cls: "anchor",
        when: fmtDate(p.died),
        what: "Died",
      });
    const life = `${yearOf(p.born)}–${yearOf(p.died)}`;
    panel.innerHTML = `<div class="pwrap">
    <div class="phead"><span class="grab" aria-hidden="true"></span><span class="phtitle"></span><button class="pclose" onclick="location.hash=''">Close</button></div>
    <button class="ptag" id="ptag" data-group="${esc(p.group)}" title="Show only ${esc(GROUP_LABEL[p.group] || p.group)} on the map"><span class="dot" style="background:var(--g-${esc(p.group)})"></span>${esc(GROUP_LABEL[p.group] || p.group)}</button>
    <h2>${esc(p.name)}</h2>
    ${(p.aka || []).length ? `<div class="aka">“${esc(p.aka.join("”, “"))}”</div>` : ""}
    <div class="dates">${life}${p.wikipedia ? ` · <a class="ext" href="${esc(p.wikipedia)}" target="_blank" rel="noopener">Wikipedia</a>` : ""}</div>
    ${p.bio ? `<p class="bio">${esc(p.bio)}</p>` : `<p class="bio" style="font-style:italic;color:var(--ink3)">Biography pending research.</p>`}
    <div class="sect">Engagements, birth to death</div>
    ${
      rows.length
        ? `<ul class="tl">${rows.map((r) => `<li class="${r.cls}"><span class="knot"></span><div class="when">${esc(r.when)}</div><div class="what">${r.what}</div></li>`).join("")}</ul>`
        : `<p class="bio" style="font-style:italic;color:var(--ink3)">No engagements recorded yet (research pending).</p>`
    }
    ${sourcesByPerson(id)}
    ${p.bio_note ? `<details class="method"><summary>Sources</summary><div>${esc(p.bio_note)}</div></details>` : ""}
  </div>`;
    $("#ptag").addEventListener("click", () => soloFromChip(p.group));
    wireSourceFilter();
    wirePanelHandle();
    showPanel();
    focusGraph({ person: id });
  }
  function openRel(id) {
    const r = RELS.find((x) => x.id === id);
    if (!r) {
      closePanel();
      return;
    }
    const [a, b] = r.people.map((pid) => P.get(pid));
    const d = r.disputed;
    PANEL_SRC = [];
    const srcCards = byEvidenceDate(r.sources || [])
      .map((q) => {
        PANEL_SRC.push({
          hay: srcHay(q, null),
          y: srcYear(q),
          doc: q.document || null,
          loc: (q.location || {}).short || null,
          q,
        });
        return quoteCard(q, null, PANEL_SRC.length - 1);
      })
      .join("");
    panel.innerHTML = `<div class="pwrap">
    <div class="phead"><span class="grab" aria-hidden="true"></span><span class="phtitle"></span><button class="pclose" onclick="location.hash=''">Close</button></div>
    <h2 class="rhead"><a href="#/p/${esc(a.id)}">${esc(a.name)}</a> &amp; <a href="#/p/${esc(b.id)}">${esc(b.name)}</a></h2>
    <div class="datesline">${esc(relDateLabel(r))}</div>
    ${certBadge(r)}
    ${r.summary ? `<p class="summary">${esc(r.summary)}</p>` : ""}
    ${(r.phases || []).length ? `<div class="sect">Phases</div><ul class="phases">${r.phases.map((ph) => `<li><b>${esc(fmtDate(ph.start))}${ph.end ? ` – ${esc(fmtDate(ph.end))}` : ""}</b>${ph.note ? ` — ${esc(ph.note)}` : ""}</li>`).join("")}</ul>` : ""}
    ${d ? `<div class="disputed"><b>Contested.</b> ${esc(d.claim || "")}${d.asserted_by ? `<div class="dline"><span>Asserted</span>${esc(d.asserted_by)}</div>` : ""}${d.disputed_by ? `<div class="dline"><span>Against</span>${esc(d.disputed_by)}</div>` : ""}${d.grounds ? `<div class="dline"><span>Grounds</span>${esc(d.grounds)}</div>` : ""}</div>` : ""}
    <div class="sect">Sources, in chronological order (${(r.sources || []).length})</div>
    ${sourceFilterBar((r.sources || []).length)}
    ${srcCards || `<p class="bio" style="font-style:italic;color:var(--ink3)">No sources recorded yet.</p>`}
    ${r.certainty_reasoning ? `<details class="method"><summary>Classification Reasoning</summary><div>${esc(r.certainty_reasoning)}</div></details>` : ""}
  </div>`;
    wireSourceFilter();
    wirePanelHandle();
    showPanel();
    focusGraph({ rel: id });
  }
  function openPair(x, y) {
    const pa = P.get(x),
      pb = P.get(y);
    if (!pa || !pb) {
      closePanel();
      return;
    }
    const flat = [];
    const rel = (byPerson.get(x) || []).find((r) => r.people.includes(y));
    if (rel)
      for (const q of rel.sources || [])
        flat.push({ q, r: rel, other: P.get(partnerOf(rel, x)) });
    const addCE = (owner, pid, other) => {
      for (const ce of owner.sexuality_sources || []) {
        if (NAME_INDEX.get(ce.subject || "") !== other) continue;
        for (const q of ce.sources || [])
          flat.push({ q, label: ce.subject, labelId: other, owner: pid });
      }
    };
    addCE(pa, x, y);
    addCE(pb, y, x);
    if (!flat.length) {
      closePanel();
      return;
    }
    if (rel)
      for (const f of flat)
        if (!f.r) {
          f.r = rel;
          f.other = P.get(partnerOf(rel, x));
        }
    const merged = [],
      byKey = new Map();
    for (const f of flat) {
      const txt = (f.q.quote || "").replace(/\W+/g, " ").trim().toLowerCase();
      if (!txt) {
        merged.push(f);
        continue;
      }
      const key = `${f.q.work}|${f.q.locator}|${txt}`;
      const first = byKey.get(key);
      if (first) (first.also = first.also || []).push(f);
      else {
        byKey.set(key, f);
        merged.push(f);
      }
    }
    PANEL_SRC = [];
    const cards = byEvidenceDate(merged, (f) => f.q)
      .map((f) => {
        PANEL_SRC.push({
          hay: srcHay(f.q, f),
          y: srcYear(f.q),
          doc: f.q.document || null,
          loc: (f.q.location || {}).short || null,
          q: f.q,
        });
        return quoteCard(f.q, f, PANEL_SRC.length - 1);
      })
      .join("");
    panel.innerHTML = `<div class="pwrap">
    <div class="phead"><span class="grab" aria-hidden="true"></span><span class="phtitle"></span><button class="pclose" onclick="location.hash=''">Close</button></div>
    <h2 class="rhead"><a href="#/p/${esc(x)}">${esc(pa.name)}</a> &amp; <a href="#/p/${esc(y)}">${esc(pb.name)}</a></h2>
    <div class="datesline">${rel ? esc(relDateLabel(rel)) : "no connection recorded"}</div>
    <div class="sect">Sources connecting them (${merged.length})</div>
    <p class="sect-note">${rel ? "Their recorded connection, plus the quotations that put the two in the same frame." : "No connection line is recorded between them; these are the quotations that put the two in the same frame."}</p>
    ${sourceFilterBar(merged.length)}
    ${cards}
  </div>`;
    wireSourceFilter();
    wirePanelHandle();
    showPanel();
  }
  function openList() {
    const sorted = [...RELS].sort(
      (x, y) => sortKey(x.start) - sortKey(y.start),
    );
    panel.innerHTML = `<div class="pwrap">
    ${isDesktop() ? "" : `<div class="phead"><span class="grab" aria-hidden="true"></span><span class="phtitle"></span><button class="pclose" onclick="location.hash=''">Close</button></div>`}
    <div class="sect">All relationships · chronological (${sorted.length})</div>
    ${sorted
      .map((r) => {
        const [a, b] = r.people.map((pid) => P.get(pid));
        let ok = 0,
          pend = 0;
        for (const q of r.sources || [])
          (q.verification || "").startsWith("verified") ? ok++ : pend++;
        return `<button class="lrow" onclick="location.hash='#/r/${esc(r.id)}'">
        <span class="when">${esc(relDateLabel(r))}</span><br>
        ${esc(a.name)} &amp; ${esc(b.name)}${miniBadge(r.certainty)}
        <span class="vs">${ok ? `(${ok})` : ""}${pend ? ` (⧖${pend})` : ""}</span>
      </button>`;
      })
      .join("")}
  </div>`;
    wirePanelHandle();
    showPanel();
    focusGraph({});
  }

  function showPanel() {
    panel.style.transition = "";
    panel.style.transform = "";
    panel.classList.add("open");
    panel.scrollTop = 0;
    wirePanelTitle();
  }

  function mountAbout() {
    const host = $("#aboutBody");
    if (!host || !WEB.about) return;
    host.innerHTML = WEB.about.replace(/\{\{line:([a-z-]+)\}\}/g, (m, c) =>
      lineSvg(SAMPLES[c]),
    );
  }
  function mountContrib() {
    const host = $("#contribBody");
    if (host && WEB.contributing) host.innerHTML = WEB.contributing;
  }
  const isDesktop = () => matchMedia("(min-width:901px)").matches;

  // Both documents render into the same panel, so they share one renderer. About is what the
  // panel falls back to on desktop with no hash; Contributing is only ever reached by its route.
  function renderDoc(id) {
    panel.innerHTML = `<div class="pwrap">
    ${isDesktop() ? "" : `<div class="phead"><span class="grab" aria-hidden="true"></span><span class="phtitle"></span><button class="pclose" onclick="location.hash=''">Close</button></div>`}
    ${$(id).innerHTML}</div>`;
    panel.classList.toggle("doc", id === "#contribBody");
    wirePanelHandle();
    showPanel();
  }
  const renderAbout = () => renderDoc("#aboutBody");
  const renderContrib = () => renderDoc("#contribBody");

  function syncAbout() {
    const h = location.hash;
    $("#btnAbout").setAttribute(
      "aria-pressed",
      String(h === "#/about" || (isDesktop() && !h)),
    );
    $("#btnContrib").setAttribute(
      "aria-pressed",
      String(h === "#/contributing"),
    );
  }
  function closePanel() {
    focusGraph({});
    if (isDesktop()) renderAbout();
    else panel.classList.remove("open");
  }
  function focusGraph({ person, rel }) {
    for (const e of edges) e.g.classList.remove("focus");
    for (const n of nodes) n.g.classList.remove("focus", "primary");

    if (person) {
      const n = N.get(person);
      if (n) n.g.classList.add("focus", "primary");
      for (const e of edges)
        if (e.r.people.includes(person)) {
          e.g.classList.add("focus");
          N.get(partnerOf(e.r, person)).g.classList.add("focus");
        }
      bringIntoView(N.get(person) ? [N.get(person)] : []);
    }
    if (rel) {
      const e = edges.find((x) => x.r.id === rel);
      if (e) {
        e.g.classList.add("focus");
        e.a.g.classList.add("focus");
        e.b.g.classList.add("focus");
        bringIntoView([e.a, e.b]);
      }
    }
    svg.classList.toggle("focusing", !!(person || rel));
  }

  let vbTween = 0;
  function stopVBTween() {
    if (vbTween) {
      cancelAnimationFrame(vbTween);
      vbTween = 0;
    }
  }
  function tweenVB(x, y, w, h, ms) {
    stopVBTween();
    if (reduceMotion) {
      vb.x = x;
      vb.y = y;
      vb.w = w;
      vb.h = h;
      applyVB();
      return;
    }
    const s = { x: vb.x, y: vb.y, w: vb.w, h: vb.h },
      t0 = performance.now(),
      D = ms || 300;
    (function step() {
      const t = Math.min(1, (performance.now() - t0) / D),
        e = 1 - Math.pow(1 - t, 3); // ease out
      vb.x = s.x + (x - s.x) * e;
      vb.y = s.y + (y - s.y) * e;
      vb.w = s.w + (w - s.w) * e;
      vb.h = s.h + (h - s.h) * e;
      applyVB();
      if (t < 1) vbTween = requestAnimationFrame(step);
      else vbTween = 0;
    })();
  }

  function bringIntoView(ns) {
    if (!ns.length) return;
    const m = 70;
    let x0 = Infinity,
      y0 = Infinity,
      x1 = -Infinity,
      y1 = -Infinity;
    for (const n of ns) {
      x0 = Math.min(x0, n.x);
      x1 = Math.max(x1, n.x);
      y0 = Math.min(y0, n.y);
      y1 = Math.max(y1, n.y);
    }
    if (
      x0 >= vb.x + m &&
      x1 <= vb.x + vb.w - m &&
      y0 >= vb.y + m &&
      y1 <= vb.y + vb.h - m
    )
      return;
    const aspect = paneAspect();
    let w = vb.w,
      h = vb.h,
      x = vb.x,
      y = vb.y;
    const tooBig = x1 - x0 + 2 * m > w || y1 - y0 + 2 * m > h;
    if (tooBig) {
      let hw = Math.max(w / 2, (x1 - x0) / 2 + m, ((y1 - y0) / 2 + m) * aspect);
      hw = Math.min(hw, (W / 2) * ZOOM_OUT_MAX);
      w = hw * 2;
      h = w / aspect;
      x = (x0 + x1) / 2 - w / 2;
      y = (y0 + y1) / 2 - h / 2;
    } else {
      if (x0 - m < x) x = x0 - m;
      if (x1 + m > x + w) x = x1 + m - w;
      if (y0 - m < y) y = y0 - m;
      if (y1 + m > y + h) y = y1 + m - h;
    }
    tweenVB(x, y, w, h);
  }

  const MIN_FOCUS_HALFW = 190;
  function fitNodes(ns, ms) {
    if (!ns.length) return;
    const m = 90;
    let x0 = Infinity,
      y0 = Infinity,
      x1 = -Infinity,
      y1 = -Infinity;
    for (const n of ns) {
      x0 = Math.min(x0, n.x);
      x1 = Math.max(x1, n.x);
      y0 = Math.min(y0, n.y);
      y1 = Math.max(y1, n.y);
    }
    const aspect = paneAspect();
    let hw = Math.max(
      (x1 - x0) / 2 + m,
      ((y1 - y0) / 2 + m) * aspect,
      MIN_FOCUS_HALFW,
    );
    hw = Math.min(hw, (W / 2) * ZOOM_OUT_MAX);
    const w = hw * 2,
      h = w / aspect;
    tweenVB((x0 + x1) / 2 - w / 2, (y0 + y1) / 2 - h / 2, w, h, ms || 420);
  }
  // A reader is a VIEW, so it gets a URL. Two things need care. Opening a reader from the router
  // must not write the hash again, or every open bounces through `hashchange` a second time -
  // hence `routing`. And closing must go back to the panel the reader was opened from rather
  // than to nothing, which `readerReturn` remembers; `history.back()` would walk off the site
  // for somebody who arrived on the link cold.
  let routing = false;
  let readerReturn = null;
  function openReaderHash(h) {
    if (routing) return;
    readerReturn = location.hash.startsWith("#/letter/") || location.hash.startsWith("#/scan/")
      ? readerReturn
      : location.hash;
    location.hash = h;
  }
  function closeReaderHash() {
    if (routing) return;
    const h = location.hash;
    if (!h.startsWith("#/letter/") && !h.startsWith("#/scan/")) return;
    location.hash = readerReturn || "";
    readerReturn = null;
  }
  // A letter_id is "letters-2000/1044#1" - a slash AND a hash, both of which a fragment would
  // read as structure. Encoded whole, so the id survives being a URL.
  const letterHash = (id) => "#/letter/" + encodeURIComponent(id);
  const scanHash = (f, n) => `#/scan/${f.archive}/${f.item}/${n}`;

  function route() {
    const h = location.hash;
    $("#btnList").setAttribute("aria-pressed", String(h === "#/list"));
    syncAbout();
    if (h.startsWith("#/pair/")) {
      const [x, y] = decodeURIComponent(h.slice(7)).split("--");
      if (x && y) openPair(x, y);
    } else if (h.startsWith("#/p/")) openPerson(decodeURIComponent(h.slice(4)));
    else if (h.startsWith("#/r/")) openRel(decodeURIComponent(h.slice(4)));
    else if (h === "#/list") openList();
    else if (h === "#/about") renderAbout();
    else if (h === "#/contributing") renderContrib();
    else if (h.startsWith("#/letter/")) {
      routing = true;
      openLetter(decodeURIComponent(h.slice(9)), null);
      routing = false;
      return; // the reader sits over whatever panel was already there; do not close it
    } else if (h.startsWith("#/scan/")) {
      const [arc, item, page] = h.slice(7).split("/").map(decodeURIComponent);
      routing = true;
      openScan(arc, item, Number(page));
      routing = false;
      return;
    } else closePanel();
    // Leaving a reader route by any means - Back, an edited URL, a click elsewhere - closes it.
    if (!LET_EL.hidden) closeLetter();
    if (!FACS_EL.hidden) closeFacsimile();
  }
  addEventListener("hashchange", route);
  $("#btnList").addEventListener("click", () => {
    location.hash = location.hash === "#/list" ? "" : "#/list";
  });

  $("#btnAbout").addEventListener("click", () => {
    location.hash = location.hash === "#/about" ? "" : "#/about";
  });
  // The legend folds away on small screens (see the media query in web.css). It stays in the
  // DOM either way, so the filter chips inside it keep working whether or not it is on screen.
  $("#btnLegend").addEventListener("click", () => {
    const open = $("#legend").classList.toggle("open");
    $("#btnLegend").setAttribute("aria-expanded", String(open));
  });
  $("#btnContrib").addEventListener("click", () => {
    location.hash = location.hash === "#/contributing" ? "" : "#/contributing";
  });
  addEventListener("resize", () => {
    if (!location.hash) closePanel();
    syncAbout();
  });
  addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && panel.classList.contains("open"))
      location.hash = "";
  });
  const vc = verCounts();
  mountAbout(); // must precede the colophon fill below: it replaces the element that holds it
  mountContrib();
  $("#stamp").textContent =
    WEB.built === "unbuilt"
      ? ""
      : `${WEB.people.length} people · ${RELS.length} connections · ✓ ${vc.ok} quotes verified, ⧖ ${vc.pend} quotes pending verification · updated ${WEB.built}`;
  $("#colophon").innerHTML =
    `Updated <b>${esc(WEB.built)}</b> · ${WEB.people.length} people, ${RELS.length} relationships, ${vc.total} source records (${vc.ok} verified, ${vc.pend} pending verification, ${vc.pointers} pointers)`;

  function nodeLineClearance(n, skip) {
    let m = Infinity;
    for (const e of edges) {
      if (e.a === n || e.b === n) continue;
      if (skip && (e.a === skip || e.b === skip)) continue;
      const x1 = e.a.x,
        y1 = e.a.y,
        dx = e.b.x - x1,
        dy = e.b.y - y1,
        L2 = dx * dx + dy * dy || 1;
      let t = ((n.x - x1) * dx + (n.y - y1) * dy) / L2;
      t = Math.max(0, Math.min(1, t));
      m = Math.min(m, Math.hypot(n.x - (x1 + t * dx), n.y - (y1 + t * dy)));
    }
    return m;
  }
  function countOnLines() {
    let c = 0;
    for (const n of nodes) if (nodeLineClearance(n) < n.r) c++;
    return c;
  }
  function countOverlaps() {
    let c = 0;
    for (let i = 0; i < nodes.length; i++)
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i],
          b = nodes[j];
        if (Math.hypot(b.x - a.x, b.y - a.y) < a.r + b.r) c++;
      }
    return c;
  }
  function rescueOnLines() {
    let onLines = countOnLines(),
      overlaps = countOverlaps();
    if (!onLines) return;
    for (const n of nodes) {
      if (n.pinned || n.hx != null) continue;
      if (nodeLineClearance(n) >= n.r) continue;
      const es = mapByPerson.get(n.id) || [];
      if (!es.length) continue;
      const anchor = N.get(partnerOf(es[0], n.id));
      if (!anchor) continue;
      const home = { x: n.x, y: n.y };
      const rest =
        (
          edges.find(
            (e) =>
              (e.a === n && e.b === anchor) || (e.b === n && e.a === anchor),
          ) || {}
        ).rest || SIM.REST;
      let best = null;
      for (const mul of [1.0, 1.3, 1.6, 1.9, 2.2, 2.6, 3.0]) {
        const rad = rest * mul;
        for (let k = 0; k < 48; k++) {
          const ang = (k * Math.PI * 2) / 48;
          const x = anchor.x + Math.cos(ang) * rad,
            y = anchor.y + Math.sin(ang) * rad;
          n.x = x;
          n.y = y; // every ring position is fair game; there is no frame to stay inside
          const lc = nodeLineClearance(n);
          if (lc < n.r + CLEAR) continue;
          let gap = Infinity;
          for (const m of nodes) {
            if (m === n) continue;
            gap = Math.min(gap, Math.hypot(m.x - n.x, m.y - n.y) - m.r - n.r);
          }
          if (gap < 10) continue;
          const score = lc + gap * 0.5 - rad * 0.06; // clear of lines and of nodes, without wandering off
          if (!best || score > best.score) best = { x, y, score };
        }
      }
      n.x = home.x;
      n.y = home.y;
      if (!best) continue;
      n.x = best.x;
      n.y = best.y;
      const nowLines = countOnLines(),
        nowOver = countOverlaps();
      if (nowLines < onLines && nowOver <= overlaps) {
        onLines = nowLines;
        overlaps = nowOver;
      } else {
        n.x = home.x;
        n.y = home.y;
      }
    }
  }

  function countCrossings() {
    let c = 0;
    const side = (ax, ay, bx, by, cx, cy) =>
      (cy - ay) * (bx - ax) - (by - ay) * (cx - ax);
    for (let i = 0; i < edges.length; i++)
      for (let j = i + 1; j < edges.length; j++) {
        const e = edges[i],
          f = edges[j];
        if (e.a === f.a || e.a === f.b || e.b === f.a || e.b === f.b) continue; // sharing a person is not a crossing
        const d1 = side(f.a.x, f.a.y, f.b.x, f.b.y, e.a.x, e.a.y),
          d2 = side(f.a.x, f.a.y, f.b.x, f.b.y, e.b.x, e.b.y),
          d3 = side(e.a.x, e.a.y, e.b.x, e.b.y, f.a.x, f.a.y),
          d4 = side(e.a.x, e.a.y, e.b.x, e.b.y, f.b.x, f.b.y);
        if (d1 > 0 !== d2 > 0 && d3 > 0 !== d4 > 0) c++;
      }
    return c;
  }

  function drawnLen(e) {
    const dx = e.b.x - e.a.x,
      dy = e.b.y - e.a.y,
      L = Math.hypot(dx, dy) || 1,
      ux = dx / L,
      uy = dy / L;
    const arrow = e.r.certainty === "attraction-expressed" && e.r.direction;
    const src = arrow && e.r.direction === e.b.id ? e.b : e.a,
      tgt = src === e.a ? e.b : e.a;
    const sx = src === e.a ? ux : -ux,
      sy = src === e.a ? uy : -uy;
    return (
      L -
      trimPastLabel(src, sx, sy, src.r) -
      trimPastLabel(tgt, -sx, -sy, tgt.r + (arrow ? 11 : 0))
    );
  }

  function spreadShortEdges() {
    const was = { c: countCrossings(), o: countOverlaps(), l: countOnLines() };
    const snap = nodes.map((n) => [n.x, n.y]);
    for (let iter = 0; iter < 80; iter++) {
      let worst = 0;
      for (const e of edges) {
        const need = MIN_EDGE - drawnLen(e);
        if (need <= 0.5) continue;
        worst = Math.max(worst, need);
        const dx = e.b.x - e.a.x,
          dy = e.b.y - e.a.y,
          L = Math.hypot(dx, dy) || 1;
        const ux = dx / L,
          uy = dy / L,
          step = Math.min(need, 5);
        const da = mapDegree(e.a.id) + 1,
          db = mapDegree(e.b.id) + 1;
        let wa = e.a.pinned ? 0 : db / (da + db),
          wb = e.b.pinned ? 0 : da / (da + db);
        const tot = wa + wb;
        if (!tot) continue;
        wa /= tot;
        wb /= tot;
        e.a.x -= ux * step * wa;
        e.a.y -= uy * step * wa;
        e.b.x += ux * step * wb;
        e.b.y += uy * step * wb;
      }
      if (worst <= 0.5) break;
      for (let i = 0; i < nodes.length; i++)
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i],
            b = nodes[j];
          boxPush(a, b, 4, (axd, ayd, bxd, byd) => {
            if (!a.pinned) {
              a.x += axd;
              a.y += ayd;
            }
            if (!b.pinned) {
              b.x += bxd;
              b.y += byd;
            }
          });
        }
    }
    const now = { c: countCrossings(), o: countOverlaps(), l: countOnLines() };
    if (now.c > was.c || now.o > was.o || now.l > was.l)
      snap.forEach(([x, y], i) => {
        nodes[i].x = x;
        nodes[i].y = y;
      });
  }
  function treeLayoutSatellites() {
    const members = new Map();
    for (const n of nodes) {
      const ci = compOf.get(n.id);
      if (ci === mainComp) continue;
      if (!members.has(ci)) members.set(ci, []);
      members.get(ci).push(n);
    }
    let best = {
      cross: countCrossings(),
      lines: countOnLines(),
      over: countOverlaps(),
    };
    for (const [, ms] of members) {
      if (ms.length < 3) continue; // a pair or a lone node has nothing to arrange
      const ids = new Set(ms.map((n) => n.id));
      const adj = new Map(ms.map((n) => [n.id, []]));
      let ecount = 0;
      for (const e of edges) {
        if (!ids.has(e.a.id) || !ids.has(e.b.id)) continue;
        adj.get(e.a.id).push(e.b.id);
        adj.get(e.b.id).push(e.a.id);
        ecount++;
      }
      if (ecount !== ms.length - 1) continue; // has a cycle: not a tree, leave it to the solver
      const root = ms.reduce(
        (a, b) => (adj.get(b.id).length > adj.get(a.id).length ? b : a),
        ms[0],
      );
      // depth and parents
      const par = new Map([[root.id, null]]),
        depth = new Map([[root.id, 0]]),
        order = [root.id];
      for (let i = 0; i < order.length; i++) {
        const u = order[i];
        for (const v of adj.get(u))
          if (!depth.has(v)) {
            par.set(v, u);
            depth.set(v, depth.get(u) + 1);
            order.push(v);
          }
      }
      const kids = new Map(ms.map((n) => [n.id, []]));
      for (const id of order) if (par.get(id)) kids.get(par.get(id)).push(id);
      // leaves below each node, which is what the angular slots are shared out by
      const leaves = new Map();
      for (let i = order.length - 1; i >= 0; i--) {
        const id = order[i],
          ks = kids.get(id);
        leaves.set(
          id,
          ks.length ? ks.reduce((s, k) => s + leaves.get(k), 0) : 1,
        );
      }
      const maxDepth = Math.max(...depth.values()) || 1;
      const cx0 = ms.reduce((s, n) => s + n.x, 0) / ms.length,
        cy0 = ms.reduce((s, n) => s + n.y, 0) / ms.length;
      const spread = Math.max(
        ...ms.map((n) => Math.hypot(n.x - cx0, n.y - cy0)),
      );
      const ring = Math.max(105, Math.min(165, spread / maxDepth));
      const home = ms.map((n) => ({ n, x: n.x, y: n.y }));
      let bestRot = null;
      for (let r = 0; r < 16; r++) {
        const rot = (r * Math.PI * 2) / 16,
          ang = new Map();
        const place = (id, a0, a1) => {
          const mid = (a0 + a1) / 2;
          ang.set(id, mid);
          const N0 = N.get(id),
            d = depth.get(id);
          N0.x = cx0 + Math.cos(mid + rot) * ring * d;
          N0.y = cy0 + Math.sin(mid + rot) * ring * d;
          let a = a0;
          for (const k of kids.get(id)) {
            const w = ((a1 - a0) * leaves.get(k)) / leaves.get(id);
            place(k, a, a + w);
            a += w;
          }
        };
        place(root.id, 0, Math.PI * 2);
        N.get(root.id).x = cx0;
        N.get(root.id).y = cy0;
        const cross = countCrossings(),
          lines = countOnLines(),
          over = countOverlaps();
        if (
          !bestRot ||
          cross < bestRot.cross ||
          (cross === bestRot.cross && over < bestRot.over)
        )
          bestRot = { rot, cross, lines, over, pos: ms.map((n) => [n.x, n.y]) };
      }
      const ok =
        bestRot &&
        bestRot.cross <= best.cross &&
        bestRot.over <= best.over &&
        bestRot.lines <= best.lines;
      if (ok) {
        bestRot.pos.forEach(([x, y], i) => {
          ms[i].x = x;
          ms[i].y = y;
        });
        best = {
          cross: bestRot.cross,
          lines: bestRot.lines,
          over: bestRot.over,
        };
      } else {
        home.forEach((h) => {
          h.n.x = h.x;
          h.n.y = h.y;
        });
      }
    }
  }

  const MIN_EDGE = 58;
  const PACK_CELL = 52;
  function packComponents() {
    const key = (i, j) => i + "," + j;
    const cellOf = (x, y) => [
      Math.floor(x / PACK_CELL),
      Math.floor(y / PACK_CELL),
    ];
    const members = new Map(),
      cedges = new Map();
    for (const n of nodes) {
      const ci = compOf.get(n.id);
      if (!members.has(ci)) members.set(ci, []);
      members.get(ci).push(n);
    }
    for (const e of edges) {
      const ci = compOf.get(e.a.id);
      if (!cedges.has(ci)) cedges.set(ci, []);
      cedges.get(ci).push(e);
    }

    const cellsOf = (ci) => {
      const s = new Set();
      for (const n of members.get(ci) || []) {
        const [i0, j0] = cellOf(n.x - n.hw, n.y - n.r),
          [i1, j1] = cellOf(n.x + n.hw, n.y + n.r + LABEL_BELOW + 3);
        for (let i = i0; i <= i1; i++)
          for (let j = j0; j <= j1; j++) s.add(key(i, j));
      }
      for (const e of cedges.get(ci) || []) {
        const dx = e.b.x - e.a.x,
          dy = e.b.y - e.a.y,
          L = Math.hypot(dx, dy) || 1;
        const steps = Math.max(1, Math.ceil(L / (PACK_CELL / 2)));
        for (let t = 0; t <= steps; t++) {
          const [i, j] = cellOf(
            e.a.x + (dx * t) / steps,
            e.a.y + (dy * t) / steps,
          );
          s.add(key(i, j));
        }
      }
      return s;
    };
    const dilate = (s) => {
      // one cell of breathing room, so nothing sits flush
      const out = new Set();
      for (const k of s) {
        const [i, j] = k.split(",").map(Number);
        for (let a = -1; a <= 1; a++)
          for (let b = -1; b <= 1; b++) out.add(key(i + a, j + b));
      }
      return out;
    };
    const occupied = dilate(cellsOf(mainComp));
    const ms = members.get(mainComp) || [];
    const hub = N.get("wilde") || ms[0];
    if (!hub) return;
    const [hi, hj] = cellOf(hub.x, hub.y);

    const cand = [];
    for (let i = -46; i <= 46; i++)
      for (let j = -46; j <= 46; j++)
        cand.push([hi + i, hj + j, i * i + j * j]);
    cand.sort((a, b) => a[2] - b[2]);
    const sats = [...members.keys()]
      .filter((ci) => ci !== mainComp)
      .sort((a, b) => members.get(b).length - members.get(a).length);
    for (const ci of sats) {
      const own = cellsOf(ci);
      const cs = members.get(ci);
      const cx = cs.reduce((s, n) => s + n.x, 0) / cs.length,
        cy = cs.reduce((s, n) => s + n.y, 0) / cs.length;
      const [oi, oj] = cellOf(cx, cy);
      const rel = [...own].map((k) => {
        const [i, j] = k.split(",").map(Number);
        return [i - oi, j - oj];
      });
      let placed = null;
      for (const [ai, aj] of cand) {
        let fits = true;
        for (const [di, dj] of rel)
          if (occupied.has(key(ai + di, aj + dj))) {
            fits = false;
            break;
          }
        if (fits) {
          placed = [ai, aj];
          break;
        }
      }
      if (!placed) continue; // nowhere in range: leave it where the solver put it
      const dx = (placed[0] - oi) * PACK_CELL,
        dy = (placed[1] - oj) * PACK_CELL;
      for (const n of cs) {
        n.x += dx;
        n.y += dy;
      }
      for (const k of dilate(cellsOf(ci))) occupied.add(k);
    }
  }
  function settleOffLines(maxIter) {
    for (let k = 0; k < maxIter; k++) {
      let worst = 0;
      for (const n of nodes) {
        if (n.pinned) continue;
        let ax = 0,
          ay = 0;
        for (const e of edges) {
          if (e.a === n || e.b === n) continue;
          const x1 = e.a.x,
            y1 = e.a.y,
            dx = e.b.x - x1,
            dy = e.b.y - y1,
            L2 = dx * dx + dy * dy || 1;
          let t = ((n.x - x1) * dx + (n.y - y1) * dy) / L2;
          t = Math.max(0, Math.min(1, t));
          const ox = n.x - (x1 + t * dx),
            oy = n.y - (y1 + t * dy),
            d = Math.hypot(ox, oy) || 0.01;
          const min = n.r + CLEAR;
          if (d < min) {
            ax += (ox / d) * (min - d);
            ay += (oy / d) * (min - d);
          }
        }
        if (!ax && !ay) continue;

        const mag = Math.hypot(ax, ay);
        if (mag > worst) worst = mag;
        const step = Math.min(mag, 3.5) / mag;
        n.x += ax * step;
        n.y += ay * step; // no walls to bounce off any more; outward is always open
      }
      for (let i = 0; i < nodes.length; i++)
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i],
            b = nodes[j];
          boxPush(a, b, 4, (axd, ayd, bxd, byd) => {
            if (!a.pinned) {
              a.x += axd;
              a.y += ayd;
            }
            if (!b.pinned) {
              b.x += bxd;
              b.y += byd;
            }
          });
        }
      if (worst < 0.5) break;
    }
  }

  if (!WEB.people.length) $("#emptymsg").hidden = false;
  applyVB();

  while (alpha > SIM.ALPHA_MIN) tick();
  settleOffLines(220);
  rescueOnLines();
  settleOffLines(60); // let the neighbours of anyone moved settle again
  treeLayoutSatellites(); // detached households are trees: draw them exactly, not approximately
  settleOffLines(40);

  spreadShortEdges(); // no connection too short to read its own line style
  packComponents(); // then pack the components into each other's gaps, DisCo-fashion

  for (const n of nodes) {
    n.cx = n.x;
    n.cy = n.y;
  }

  function paneAspect() {
    const rect = svg.getBoundingClientRect();
    return rect.width && rect.height ? rect.width / rect.height : W / H;
  }

  const OPEN_SCALE = 1.45; // how much wider than W the opening frame is; see openOnHub
  function openOnHub() {
    if (!nodes.length) return;
    const hub =
      N.get("wilde") ||
      nodes.reduce(
        (a, b) => (mapDegree(b.id) > mapDegree(a.id) ? b : a),
        nodes[0],
      );
    const hw = (W * OPEN_SCALE) / 2,
      hh = hw / paneAspect();
    vb.w = hw * 2;
    vb.h = hh * 2;
    vb.x = hub.x - hw;
    vb.y = hub.y - hh;
    applyVB();
  }
  function fitAll() {
    if (!nodes.length) return;
    let x0 = Infinity,
      y0 = Infinity,
      x1 = -Infinity,
      y1 = -Infinity;
    for (const n of nodes) {
      const p = 24;
      x0 = Math.min(x0, n.x - n.hw - p);
      x1 = Math.max(x1, n.x + n.hw + p);
      y0 = Math.min(y0, n.y - n.r - p);
      y1 = Math.max(y1, n.y + n.r + LABEL_BELOW + p);
    }
    const aspect = paneAspect();
    let hw = Math.max((x1 - x0) / 2, ((y1 - y0) / 2) * aspect),
      hh = hw / aspect;
    const cx = (x0 + x1) / 2,
      cy = (y0 + y1) / 2;
    vb.w = hw * 2;
    vb.h = hh * 2;
    vb.x = cx - hw;
    vb.y = cy - hh;
    applyVB();
  }
  openOnHub();
  $("#btnFit").addEventListener("click", () => {
    stopVBTween();
    fitAll();
  });

  if (zoomRange)
    zoomRange.addEventListener("input", () => {
      stopVBTween();
      const r = svg.getBoundingClientRect();
      sliderDriving = true;
      zoomAbout(
        sliderToScale(+zoomRange.value),
        r.left + r.width / 2,
        r.top + r.height / 2,
      );
      sliderDriving = false;
    });
  addEventListener("resize", () => {
    // the pane's aspect drives both frames; a resize invalidates them
    const hw = vb.w / 2,
      hh = hw / paneAspect();
    vb.y += vb.h / 2 - hh;
    vb.h = hh * 2;
    applyVB();
  });
  if (reduceMotion) {
    render();
  } else {
    const SETTLE_MS = 620,
      cx = W / 2,
      cy = H / 2;
    const hash = (s) => {
      const v = Math.sin(s) * 43758.5453;
      return v - Math.floor(v);
    };
    const home = nodes.map((n, i) => {
      const dx = n.x - cx,
        dy = n.y - cy,
        r = Math.hypot(dx, dy) || 1;
      // a small inward bias, so the whole thing does open outwards ...
      const inward = 0.022 * r,
        ia = Math.atan2(dy, dx);
      // ... but a larger per-node component in its own direction, which is what stops the motion
      // being a uniform scale about the centre (i.e. a zoom).
      const wa = hash(i * 3.7) * Math.PI * 2,
        wm = 9 + hash(i * 11.3) * 11;
      return {
        n,
        x: n.x,
        y: n.y,
        ox: -Math.cos(ia) * inward + Math.cos(wa) * wm,
        oy: -Math.sin(ia) * inward + Math.sin(wa) * wm,
        delay: hash(i * 7.1) * 0.36,
      };
    });
    for (const h of home) {
      h.n.x = h.x + h.ox;
      h.n.y = h.y + h.oy;
    }
    const t0 = performance.now();
    (function settleIn(now) {
      const u = (now - t0) / SETTLE_MS;
      for (const h of home) {
        const t = Math.min(1, Math.max(0, (u - h.delay) / (1 - h.delay))),
          e = 1 - Math.pow(1 - t, 3);
        h.n.x = h.x + h.ox * (1 - e);
        h.n.y = h.y + h.oy * (1 - e);
      }
      render();
      if (u < 1) requestAnimationFrame(settleIn);
    })(t0);
  }
  // ============ the manuscript reader ============
  // A quotation is a transcription, and a transcription is a claim. This puts the document
  // behind it one click away: the letter in the writer's own hand, at the resolution the archive
  // released, with the shelfmark and the rights marker the archive attached to it.
  //
  // The pages a source names are the pages of the LETTER. The rest of the archival folder is
  // reachable behind them, greyed in the thumbnail strip, because a folder is how the papers
  // are actually kept and the boundary between one letter and the next is a reading, not a fact
  // recorded in the metadata.
  const FACS_EL = $("#facs"),
    FACS_IMG = $("#facsImg"),
    FACS_STAGE = $("#facsStage");
  let facsPages = [], // what the reader is currently showing, letter pages first
    facsAt = 0,
    facsZoomed = false,
    facsReturn = null; // the button that opened it, so focus goes back where it came from

  const ARCHIVES = WEB.archives || {};
  // `{pointer}` is how nearly every archive addresses one image - a CONTENTdm id, a NYPL image id,
  // a IIIF service id. An archive that instead paginates its facsimile, as the Morgan does 1..50,
  // has no such token, and its URL wants the page number; `{page}` is for those. A template names
  // whichever it needs, and an archive using neither (the Library of Congress publishes one item
  // page and no per-image page) is left unchanged and links every sheet to the item.
  const fill = (tpl, p) =>
    tpl && p
      ? tpl
          .replace("{pointer}", encodeURIComponent(p.pointer || ""))
          .replace("{page}", encodeURIComponent(p.n || ""))
      : "";
  // The pages are served by the archive that made them, over IIIF, not copied here. `size` is a
  // IIIF Image API size parameter: "full" for the sheet at the resolution the archive released,
  // "240," for a thumbnail 240px wide. Asking the archive for the small one keeps a 95-sheet
  // folder's filmstrip from pulling thirty megabytes to draw a row of stamps.
  //
  // Width-only, NOT the "!240,240" fit-in-a-box form: the Ransom Center advertises IIIF Image
  // level 1, which has sizeByW but not sizeByConfinedWh, and answers the confined form with a
  // broken image rather than an error.
  const iiif = (arc, p, size) => {
    const base = fill(arc.iiif_url, p);
    return base ? `${base}/full/${size}/0/default.jpg` : "";
  };

  // A source cites an archive, an item and page numbers. Everything else about those pages -
  // file, shelfmark, pointer, rights - lives once in the bundle's archive index.
  function facsItem(f) {
    const arc = ARCHIVES[f.archive] || {};
    return { arc, item: (arc.items || {})[f.item] || { pages: [] } };
  }
  function openFacsimile(f, startAt) {
    const { arc, item } = facsItem(f);
    const wanted = new Set(f.pages || []);
    // The letter's own pages, then the remainder of the folder. `rest` is flagged so the strip
    // can show where the quoted document stops and its neighbours begin.
    const own = item.pages
      .filter((p) => wanted.has(p.n))
      .map((p) => ({ ...p, rest: false }));
    if (!own.length) return;
    const rest = item.pages
      .filter((p) => !wanted.has(p.n))
      .map((p) => ({ ...p, rest: true }));
    facsPages = own.concat(rest);
    facsAt = Math.max(0, Math.min(startAt || 0, facsPages.length - 1));
    FACS_EL.facs = { f, arc, item };
    FACS_EL.hidden = false;
    document.body.style.overflow = "hidden";
    setZoom(false);
    drawThumbs();
    showPage(facsAt);
    openReaderHash(scanHash(f, (facsPages[facsAt] || {}).n));
    $("#facsClose").focus();
  }
  // From a link, all we have is an archive, an item and a page. Prefer the facsimile block of a
  // source that actually cites those pages, so the reader groups the letter's own sheets ahead of
  // the rest of the folder exactly as it would have from the card; fall back to the bare page.
  function openScan(archive, item, page) {
    const cited = FACS.find(
      (f) => f.archive === archive && String(f.item) === String(item) &&
        (f.pages || []).includes(page),
    );
    const f = cited || { archive, item, pages: [page] };
    const { item: it } = facsItem(f);
    if (!(it.pages || []).some((pp) => pp.n === page)) return;
    openFacsimile(f, Math.max(0, (f.pages || []).indexOf(page)));
  }
  function closeFacsimile() {
    closeReaderHash();
    FACS_EL.hidden = true;
    document.body.style.overflow = "";
    FACS_IMG.removeAttribute("src"); // let a 300 KB scan go rather than hold every one opened
    if (facsReturn && document.contains(facsReturn)) facsReturn.focus();
    facsReturn = null;
  }
  function showPage(i) {
    if (!facsPages.length) return;
    facsAt = (i + facsPages.length) % facsPages.length;
    const p = facsPages[facsAt],
      { f, arc, item } = FACS_EL.facs,
      of = item.pages.length;
    if (!routing && !FACS_EL.hidden && location.hash.startsWith("#/scan/")) {
      history.replaceState(null, "", scanHash(f, p.n));
    }
    FACS_STAGE.classList.add("loading");
    FACS_IMG.src = iiif(arc, p, "full");
    FACS_IMG.alt = `Manuscript page ${p.n}${p.shelfmark ? `, shelfmark ${p.shelfmark}` : ""}`;
    setZoom(false);

    const own = facsPages.filter((x) => !x.rest).length;
    $(".fname").textContent = item.title || arc.collection || "Manuscript";
    $(".fpager").textContent = p.rest
      ? `Page ${p.n} of ${of} · elsewhere in the folder`
      : `Page ${facsAt + 1} of ${own}${own < of ? ` · folder page ${p.n} of ${of}` : ""}`;

    const rec = fill(arc.record_url, p);
    $(".fcite").innerHTML = [
      p.shelfmark ? `<b>${esc(p.shelfmark)}</b>` : "",
      item.box_folder ? esc(item.box_folder) : "",
      arc.name ? esc(arc.name) : "",
      rec
        ? `<a href="${esc(rec)}" target="_blank" rel="noopener">Archive record</a>`
        : "",
      f.caption ? esc(f.caption) : "",
    ]
      .filter(Boolean)
      .join(" · ");
    // NoC-US is the archive saying the image is free of copyright in the United States.
    // Undetermined means they have not resolved it - shown plainly, because a reader who wants
    // to reuse the scan needs the archive's own answer, not ours.
    const noc = /NoC|NKC/.test(p.rights || "");
    $(".frights").innerHTML = p.rights_label
      ? `<a class="rmark${noc ? " rnoc" : ""}" href="${esc(p.rights)}" target="_blank" rel="noopener">${esc(p.rights_label)}</a>`
      : "";
    for (const t of $("#facsThumbs").children)
      if (t.dataset.i != null)
        t.setAttribute("aria-current", String(+t.dataset.i === facsAt));
    const cur = $(`#facsThumbs [data-i="${facsAt}"]`);
    if (cur) cur.scrollIntoView({ block: "nearest", inline: "nearest" });
  }
  function drawThumbs() {
    const strip = $("#facsThumbs");
    strip.textContent = "";
    if (facsPages.length < 2) return;
    facsPages.forEach((p, i) => {
      if (p.rest && !facsPages[i - 1].rest)
        strip.insertAdjacentHTML(
          "beforeend",
          `<span class="fgap">the rest of the folder</span>`,
        );
      const b = document.createElement("button");
      b.className = "fthumb" + (p.rest ? " frest" : "");
      b.dataset.i = i;
      b.title = p.shelfmark || `Page ${p.n}`;
      b.setAttribute("aria-label", `Page ${p.n}`);
      // loading="lazy" matters here: the biggest folder is 95 sheets, and the strip would
      // otherwise pull thirty megabytes to draw a row of thumbnails.
      b.innerHTML = `<img src="${esc(iiif(FACS_EL.facs.arc, p, "240,"))}" alt="" loading="lazy" decoding="async">`;
      b.addEventListener("click", () => showPage(i));
      strip.appendChild(b);
    });
  }
  function setZoom(on) {
    facsZoomed = !!on;
    FACS_STAGE.classList.toggle("zoomed", facsZoomed);
    $("#facsZoom").setAttribute("aria-pressed", String(facsZoomed));
  }
  // Zoom to a POINT, not to the middle. The reader clicks the word they want to see, so the
  // scroll lands where their eye already is rather than at the centre of the sheet.
  function zoomAt(clientX, clientY) {
    const r = FACS_IMG.getBoundingClientRect();
    const fx = r.width ? (clientX - r.left) / r.width : 0.5,
      fy = r.height ? (clientY - r.top) / r.height : 0.5;
    setZoom(true);
    const s = FACS_STAGE;
    s.scrollLeft = fx * FACS_IMG.offsetWidth - s.clientWidth / 2;
    s.scrollTop = fy * FACS_IMG.offsetHeight - s.clientHeight / 2;
  }
  FACS_IMG.addEventListener("load", () => {
    FACS_STAGE.classList.remove("loading", "failed");
  });
  // The pages come from the archive's server, so they can fail in ways a local file cannot: the
  // service down, the collection reorganised, a reader offline. Say which, and keep the record
  // link reachable - the citation under the page is still good even when the image is not.
  FACS_IMG.addEventListener("error", () => {
    if (!FACS_IMG.getAttribute("src")) return; // cleared on close, not a failure
    FACS_STAGE.classList.remove("loading");
    FACS_STAGE.classList.add("failed");
  });
  FACS_STAGE.addEventListener("click", (ev) => {
    if (dragMoved) return; // a drag that ends on the page is not a click on it
    if (facsZoomed) setZoom(false);
    else if (ev.target === FACS_IMG) zoomAt(ev.clientX, ev.clientY);
    else closeFacsimile(); // the margin around the sheet dismisses, as an overlay should
  });
  // Drag to pan. Pointer events cover mouse, pen and touch in one path, and setPointerCapture
  // keeps the drag alive when the cursor leaves the stage mid-pull.
  let dragFrom = null,
    dragMoved = false;
  FACS_STAGE.addEventListener("pointerdown", (ev) => {
    dragMoved = false;
    if (!facsZoomed || ev.button) return;
    dragFrom = {
      x: ev.clientX,
      y: ev.clientY,
      l: FACS_STAGE.scrollLeft,
      t: FACS_STAGE.scrollTop,
    };
    FACS_STAGE.setPointerCapture(ev.pointerId);
    FACS_STAGE.classList.add("dragging");
  });
  FACS_STAGE.addEventListener("pointermove", (ev) => {
    if (!dragFrom) return;
    const dx = ev.clientX - dragFrom.x,
      dy = ev.clientY - dragFrom.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) dragMoved = true;
    FACS_STAGE.scrollLeft = dragFrom.l - dx;
    FACS_STAGE.scrollTop = dragFrom.t - dy;
  });
  for (const e of ["pointerup", "pointercancel"])
    FACS_STAGE.addEventListener(e, () => {
      dragFrom = null;
      FACS_STAGE.classList.remove("dragging");
    });
  $("#facsPrev").addEventListener("click", () => showPage(facsAt - 1));
  $("#facsNext").addEventListener("click", () => showPage(facsAt + 1));
  $("#facsZoom").addEventListener("click", () => {
    if (facsZoomed) setZoom(false);
    else {
      const r = FACS_IMG.getBoundingClientRect();
      zoomAt(r.left + r.width / 2, r.top + r.height / 2);
    }
  });
  $("#facsClose").addEventListener("click", closeFacsimile);
  document.addEventListener("click", (ev) => {
    // Either chip solos its own facet. A location chip may wrap a link to the archive's record;
    // that link keeps its click, because following it is the more specific intent.
    for (const a of Object.values(FACETS)) {
      const c =
        ev.target.closest &&
        ev.target.closest(`.chip.${a.attr}[data-${a.attr}]`);
      if (!c || !reapplySrcFilter) continue;
      if (ev.target.closest("a")) return;
      soloFacet(a, c.dataset[a.attr]);
      reapplySrcFilter();
      if (a.off.size) c.scrollIntoView({ block: "nearest" }); // the card may have moved
      return;
    }
  });
  document.addEventListener("click", (ev) => {
    const b = ev.target.closest && ev.target.closest(".qfacs");
    if (!b) return;
    if (b.dataset.letter) {
      openLetter(b.dataset.letter, b);
      return;
    }
    const f = FACS[+b.dataset.facs];
    if (!f) return;
    facsReturn = b;
    openFacsimile(f, 0);
  });

  // ---- the letter reader ---------------------------------------------------------------------
  const LET_EL = $("#letter"),
    LET_TEXT = $("#letterText"),
    LET_NOTE = $("#letterNote"),
    LET_FACS = $("#letterFacs");
  let letterReturn = null;
  // Find the quoted passage inside the whole letter and mark it. A quotation is an excerpt joined
  // by ellipses, so each RUN between the ellipses is located separately and the gaps between them
  // are what the cut dropped - which is the thing the reader opened this to see. Matching is done
  // on a folded copy (spacing and quote marks normalised, since a transcription keeps the
  // document's line breaks and a card's quote does not) with an index back to the real text, so a
  // near-miss simply fails to mark rather than corrupting the letter.
  function markQuoted(full, quote) {
    // Matched on WORDS ALONE - letters, digits, single spaces, lowercased. Punctuation is dropped
    // rather than normalised because the two texts are allowed to disagree about it and often do:
    // the card quotes the printed edition, the transcription is what the manuscript says, and the
    // whole reason for reading the document was that the editors normalise. On p. 1044 the volume
    // has "Yes: I have no doubt we shall win, but the road is long" where the sheet has "Yes! …
    // win — but". Anything stricter would fail to mark the passage exactly where the difference
    // is most worth seeing. A difference in WORDS still fails, and should.
    const fold = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, " ");
    const map = [];
    let flat = "";
    for (let i = 0; i < full.length; i++) {
      const f = fold(full[i]);
      if (!f) continue;
      if (f === " ") {
        if (flat.endsWith(" ") || !flat) continue;
        flat += " ";
        map.push(i);
        continue;
      }
      flat += f;
      map.push(i);
    }
    const runs = [];
    let from = 0;
    for (const raw of quote.split(/\s*(?:…|\.\.\.)\s*/)) {
      const probe = fold(raw).trim();
      if (probe.length < 12) continue;
      const at = flat.indexOf(probe, from);
      if (at < 0) continue;
      runs.push([map[at], map[at + probe.length - 1] + 1]);
      from = at + probe.length;
    }
    if (!runs.length) return { html: esc(full), marked: false };
    let out = "",
      cur = 0;
    for (const [a, b] of runs) {
      out += esc(full.slice(cur, a)) + `<mark>${esc(full.slice(a, b))}</mark>`;
      cur = b;
    }
    return { html: out + esc(full.slice(cur)), marked: true };
  }
  function drawLetter(t, q) {
    const fac = t.transcribed_from === "facsimile";
    // The bar carries IDENTITY, and it is BUILT FROM FIELDS. It was briefly cut out of the
    // `context` paragraph instead, which meant a regex that had to know about initials ("Wilde to
    // G. H. Kersley") and abbreviations ("p. 1044"), and a browser new enough for lookbehind —
    // all to recover four values the transcriber knew when they wrote the file. The commentary in
    // `context` is not repeated here: the card this reader opened from is already showing it.
    //
    // `dated` keeps the volume's own wording, brackets and all, because "[? April 1889]" is the
    // editors saying how sure they are and a normalised date would throw that away.
    const ident = [
      `${t.sender || "Wilde"} to ${t.addressee || "—"}`,
      fmtLetterDating(t),
      (t.written || {}).from,
    ]
      .filter(Boolean)
      .join(", ");
    $(".lname", LET_EL).textContent = ident;
    $(".lwhen", LET_EL).textContent = t.printed
      ? `${(WEB.works[t.printed.work] || {}).short_cite || t.printed.work}, ${t.printed.locator}`
      : "";
    const { html, marked } =
      q && q.quote
        ? markQuoted(t.quote, q.quote)
        : { html: esc(t.quote), marked: false };
    LET_TEXT.innerHTML = html
      .split(/\n{2,}/)
      .map((p) => `<p>${fmtEmphasis(p).replace(/\n/g, "<br>")}</p>`)
      .join("");
    // What this text can and cannot settle. A transcription read off the images is a witness to
    // emphasis; one retyped from the edition is not, and saying so here is the same distinction
    // the card's chips make about the document itself.
    // One line stays: whether this text can be trusted for emphasis is the reader's business and
    // is a sentence long. The reading notes behind it are the transcriber's business - which
    // dashes were restored, what the descender of an 'f' settles - and run to a paragraph that
    // would dwarf a short letter. Collapsed, not dropped.
    const notes = [t.transcription_note, t.original_provenance].filter(Boolean);
    LET_NOTE.innerHTML =
      `<p><b>${fac ? "Transcribed from the original manuscript." : "Transcribed from the printed edition."}</b> ` +
      (fac
        ? "Any emphasis marks are the writer's own and are faithfully reproduced here."
        : "The writer's emphasis markings have been normalized and may not match the original written document.") +
      (marked ? " The passage the card quotes is highlighted." : "") +
      `</p>` +
      // `inferred` says the date is not written on the document — somebody worked it out, which is
      // precision, which is why the header states the date plainly and the qualification lives
      // here. Named per act, because a letter can have one dated and another supplied.
      (() => {
        const sup = ["written", "sent", "postmarked", "received"].filter(
          (a) => ((t[a] || {}).date || {}).inferred,
        );
        return sup.length
          ? `<p>The ${sup.join(" and ")} date${sup.length > 1 ? "s are" : " is"} the editors', ` +
            `not the writer's — supplied in the edition rather than written on the document.</p>`
          : "";
      })() +
      (notes.length
        ? `<details><summary>How it was read</summary><div>${notes
            .map((n) => `<p>${esc(n)}</p>`)
            .join("")}</div></details>`
        : "");
    LET_FACS.hidden = !t.facsimile;
    LET_FACS.onclick = t.facsimile
      ? () => {
          closeLetter();
          facsReturn = letterReturn;
          openFacsimile(t.facsimile, 0);
        }
      : null;
  }
  function openLetter(id, from) {
    letterReturn = from || null;
    const show = () => {
      const t = (LETTERS || {})[id];
      if (!t) return;
      // The card the button sits on, so the quotation can be marked inside the letter. Cards are
      // rebuilt on every filter keystroke, so it is read from the DOM at click time.
      const card = from && from.closest && from.closest("[data-si]");
      const q = card ? (PANEL_SRC[+card.dataset.si] || {}).q : null;
      drawLetter(t, q);
      openReaderHash(letterHash(id));
      LET_EL.hidden = false;
      document.body.style.overflow = "hidden";
      $("#letterClose").focus();
    };
    if (LETTERS) return show();
    fetch("data/transcriptions.json")
      .then((r) => r.json())
      .then((d) => {
        LETTERS = d.letters || {};
        show();
      })
      .catch(() => {});
  }
  function closeLetter() {
    closeReaderHash();
    LET_EL.hidden = true;
    document.body.style.overflow = "";
    if (letterReturn && document.contains(letterReturn)) letterReturn.focus();
    letterReturn = null;
  }
  $("#letterClose").addEventListener("click", closeLetter);
  addEventListener("keydown", (ev) => {
    if (!LET_EL.hidden && ev.key === "Escape") closeLetter();
  });
  addEventListener("keydown", (ev) => {
    if (FACS_EL.hidden) return;
    const k = ev.key;
    if (k === "Escape") facsZoomed ? setZoom(false) : closeFacsimile();
    else if (k === "ArrowRight") showPage(facsAt + 1);
    else if (k === "ArrowLeft") showPage(facsAt - 1);
    else if (k === "+" || k === "=") $("#facsZoom").click();
    else if (k === "-" || k === "_") setZoom(false);
    else return;
    ev.preventDefault();
    ev.stopPropagation(); // the map and the panel both listen for Escape
  });

  applyFilters();
  route();

  window.web = {
    WEB,
    nodes,
    edges,
    RELS,
    P,
    byPerson,
    applyFilters,
    byEvidenceDate,
    offGroups,
    offCerts,
    route,
    parseExchange,
  };
})();
