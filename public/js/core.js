/* INSTAR core. Progress key instar.v1 is sacred. */
(function () {
  const KEY = "instar.v1";
  const PREFS = "instar.prefs.v1";
  const ORDER = ["hello", "nymph", "soil", "tunnel", "song", "prime", "liber", "emerge"];
  const LABELS = {
    hello: "Hello",
    nymph: "Nymph",
    soil: "Soil",
    tunnel: "Tunnel",
    song: "Song",
    prime: "Prime",
    liber: "Liber",
    emerge: "Emerge",
  };
  const PATHS = {
    hello: "/",
    nymph: "/nymph/",
    soil: "/soil/",
    tunnel: "/tunnel/",
    song: "/song/",
    prime: "/prime/",
    liber: "/liber/",
    emerge: "/emerge/",
  };
  /* Habit only. Never a URL. */
  const LISTEN = {
    hello: "The first molt is not on this page.",
    nymph: "A volume waits. Count from one.",
    soil: "The least bit is a trench.",
    tunnel: "Do not listen. Look.",
    song: "Two primes, then a door.",
    prime: "Sound the marks. Do not invent.",
    liber: "Three words you already met.",
    emerge: "An unused door is a file, not a picture.",
  };

  function load() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "{}");
    } catch {
      return {};
    }
  }
  function save(state) {
    localStorage.setItem(KEY, JSON.stringify(state));
  }
  function prefs() {
    try {
      return Object.assign({ listen: false, rail: false }, JSON.parse(localStorage.getItem(PREFS) || "{}"));
    } catch {
      return { listen: false, rail: false };
    }
  }
  function savePrefs(p) {
    localStorage.setItem(PREFS, JSON.stringify(p));
  }
  function mark(id) {
    const s = load();
    s[id] = true;
    save(s);
    applySkin();
    return s;
  }
  function has(id) {
    return !!load()[id];
  }
  function depth() {
    const s = load();
    return ORDER.reduce((n, id) => n + (s[id] ? 1 : 0), 0);
  }
  function nextId() {
    const s = load();
    for (const id of ORDER) if (!s[id]) return id;
    return "emerge";
  }
  function nextHint() {
    return LISTEN[nextId()] || "";
  }
  function norm(s) {
    return String(s || "")
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "");
  }
  async function sha256(s) {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(norm(s)));
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  async function check(name, guess) {
    const want = (window.INSTAR_PUZZLE && window.INSTAR_PUZZLE.hashes[name]) || "";
    const got = await sha256(guess);
    return want && got === want;
  }

  function xPill() {
    return (
      '<a class="x-follow" href="https://x.com/suddenlyjon" target="_blank" rel="noopener noreferrer" aria-label="Follow @suddenlyjon on X" title="Follow @suddenlyjon on X">' +
      '<span class="x-follow-mark"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.9 1.5h3.5l-7.7 8.8L24 22.5h-7.4l-5.8-7.6-6.6 7.6H.7l8.2-9.4L0 1.5h7.6l5.3 7 6-7z"/></svg></span></a>'
    );
  }

  function applySkin(active) {
    const d = depth();
    document.documentElement.setAttribute("data-depth", String(d));
    document.body.classList.toggle("has-depth", d > 1);
    document.body.classList.toggle("has-rail", !!prefs().rail);
    if (active) {
      document.body.classList.toggle("page-hello", active === "hello");
      document.body.setAttribute("data-stage", active);
    }
    mountMolt(active);
    mountGuide();
  }

  function mountMolt(active) {
    let rail = document.querySelector(".molt-rail");
    if (!prefs().rail) {
      if (rail) rail.remove();
      return;
    }
    if (!rail) {
      rail = document.createElement("nav");
      rail.className = "molt-rail";
      rail.setAttribute("aria-label", "Skins shed");
      document.body.appendChild(rail);
    }
    const s = load();
    const n = depth();
    rail.innerHTML = ORDER.map(function (id) {
      const name = LABELS[id];
      if (s[id]) {
        const now = active === id ? " now" : "";
        return (
          '<a class="on' +
          now +
          '" href="' +
          PATHS[id] +
          '" title="skin shed"><span class="sr-only">' +
          name +
          "</span></a>"
        );
      }
      return '<span title="unworn"><span class="sr-only">unworn</span></span>';
    }).join("");
    rail.setAttribute("aria-label", n + " of " + ORDER.length + " skins shed");
  }

  function mountGuide() {
    let line = document.querySelector(".guide-line");
    const on = prefs().listen;
    if (!on) {
      if (line) line.remove();
      return;
    }
    if (!line) {
      line = document.createElement("p");
      line.className = "guide-line";
      const top = document.getElementById("top");
      if (top) top.insertAdjacentElement("afterend", line);
      else document.body.insertBefore(line, document.body.firstChild);
    }
    line.textContent = nextHint();
  }

  function toggleListen() {
    const p = prefs();
    p.listen = !p.listen;
    savePrefs(p);
    mountGuide();
    const btn = document.getElementById("listen-btn");
    if (btn) {
      btn.setAttribute("aria-pressed", p.listen ? "true" : "false");
      btn.textContent = p.listen ? "Listening" : "Listen";
    }
  }

  function toggleRail() {
    const p = prefs();
    p.rail = !p.rail;
    savePrefs(p);
    const stage = document.body.getAttribute("data-stage") || "";
    applySkin(stage);
    const btn = document.getElementById("skins-btn");
    if (btn) {
      btn.setAttribute("aria-pressed", p.rail ? "true" : "false");
      btn.textContent = p.rail ? "Showing skins" : "Skins";
    }
  }

  function ensureShed() {
    let el = document.querySelector(".molt-shed");
    if (el) return el;
    el = document.createElement("div");
    el.className = "molt-shed";
    el.hidden = true;
    el.innerHTML = '<p class="husk">The molt holds.</p>';
    document.body.appendChild(el);
    return el;
  }

  function flashMolt(done) {
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      done();
      return;
    }
    const el = ensureShed();
    el.hidden = false;
    requestAnimationFrame(function () {
      el.setAttribute("data-open", "true");
    });
    window.setTimeout(function () {
      el.removeAttribute("data-open");
      window.setTimeout(function () {
        el.hidden = true;
        done();
      }, 280);
    }, 640);
  }

  function registerPwa() {
    if (!("serviceWorker" in navigator)) return;
    if (location.protocol !== "https:" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1")
      return;
    navigator.serviceWorker.register("/sw.js").catch(function () {});
  }

  function mountChrome(active) {
    const top = document.getElementById("top");
    if (!top) return;
    const links = [
      ["/", "Hello", "hello"],
      ["/workbench/", "Workbench", "workbench"],
      ["/manual/", "Manual", "manual"],
    ];
    top.innerHTML =
      '<div class="brand-island">' +
      xPill() +
      '<a class="wordmark" href="/">INSTAR</a></div>' +
      '<nav class="nav" aria-label="Primary">' +
      links
        .map(([href, label, id]) => {
          const cur = id === active ? ' aria-current="page"' : "";
          return '<a href="' + href + '"' + cur + ">" + label + "</a>";
        })
        .join("") +
      "</nav>";
    applySkin(active);
    registerPwa();
  }

  function mountFoot() {
    const el = document.getElementById("foot");
    if (!el) return;
    const on = prefs().listen;
    const skins = !!prefs().rail;
    el.innerHTML =
      '<span>Original work. Not Cicada 3301. A school, not a recruiter.</span>' +
      '<span class="habits">' +
      '<button type="button" id="listen-btn" aria-pressed="' +
      (on ? "true" : "false") +
      '" title="Name the next habit, never the answer">' +
      (on ? "Listening" : "Listen") +
      "</button>" +
      '<button type="button" id="skins-btn" aria-pressed="' +
      (skins ? "true" : "false") +
      '" title="Show skins shed. Off by default. Names stay unspoken.">' +
      (skins ? "Showing skins" : "Skins") +
      "</button>" +
      '<a href="/workbench/">Workbench</a>' +
      '<a href="/manual/">Field manual</a></span>';
    const btn = document.getElementById("listen-btn");
    if (btn) btn.addEventListener("click", toggleListen);
    const skinsBtn = document.getElementById("skins-btn");
    if (skinsBtn) skinsBtn.addEventListener("click", toggleRail);
  }

  function bindGate(opts) {
    const form = document.getElementById(opts.form);
    const input = document.getElementById(opts.input);
    const status = document.getElementById(opts.status);
    const brief = document.getElementById(opts.brief);
    if (!form || !input) return;
    if (has(opts.stage) && brief) brief.hidden = false;
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const ok = await check(opts.hash, input.value);
      if (ok) {
        mark(opts.stage);
        if (status) {
          status.className = "note ok";
          status.textContent = opts.okText || "The molt holds.";
        }
        if (brief) brief.hidden = false;
        if (opts.next) {
          flashMolt(function () {
            location.href = opts.next;
          });
        }
      } else if (status) {
        status.className = "note bad";
        status.textContent = "The husk is empty. Look again.";
      }
    });
  }

  window.INSTAR = {
    ORDER,
    LABELS,
    PATHS,
    load,
    save,
    mark,
    has,
    depth,
    nextId,
    nextHint,
    prefs,
    norm,
    sha256,
    check,
    mountChrome,
    mountFoot,
    bindGate,
    xPill,
    toggleListen,
    toggleRail,
  };
})();
