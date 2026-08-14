/* INSTAR workbench: living laboratory. Tools rust in the open. */
(function () {
  const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  const TOOLS = ["classical", "book", "stego", "spec", "rsa", "runes", "hash"];

  function $(id) {
    return document.getElementById(id);
  }
  function val(id) {
    const el = $(id);
    return el ? el.value : "";
  }
  function setText(id, t) {
    const el = $(id);
    if (el) el.textContent = t;
  }
  function reduced() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  const hist = [];
  function pushHist(tool, text) {
    const line = String(text || "").replace(/\s+/g, " ").slice(0, 140);
    if (!line) return;
    hist.unshift({ tool: tool, text: line });
    if (hist.length > 12) hist.pop();
    const ol = $("hist");
    if (!ol) return;
    ol.innerHTML = hist
      .map(function (h) {
        return "<li><strong>" + h.tool + "</strong> " + escapeHtml(h.text) + "</li>";
      })
      .join("");
  }
  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function exportText(name, text) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    setTimeout(function () {
      URL.revokeObjectURL(a.href);
    }, 1000);
  }

  function selectTool(id, fromHash) {
    if (TOOLS.indexOf(id) < 0) id = "classical";
    document.querySelectorAll("#tabs [role='tab']").forEach(function (btn) {
      const on = btn.dataset.tab === id;
      btn.setAttribute("aria-selected", on ? "true" : "false");
      btn.setAttribute("tabindex", on ? "0" : "-1");
    });
    document.querySelectorAll(".panel").forEach(function (p) {
      p.hidden = p.id !== id;
    });
    if (!fromHash) {
      history.replaceState(null, "", "#" + id);
    }
    const tab = document.querySelector('#tabs [data-tab="' + id + '"]');
    if (tab && document.activeElement && document.activeElement.closest("#tabs")) tab.focus();
  }

  function specOpts() {
    return {
      nfft: Number(val("p-nfft")) || 2048,
      hop: Number(val("p-hop")) || 512,
      gain: Number(val("p-gain")) || 80,
    };
  }

  function applyClassical() {
    const C = window.INSTAR_CIPHERS;
    if (!C) return;
    const src = val("c-in");
    const key = val("c-key");
    const mode = val("c-mode");
    let out = src;
    if (mode === "atbash") out = C.atbash(src);
    else if (mode === "rot13") out = C.rot13(src);
    else if (mode === "caesar-enc") out = C.caesar(src, key);
    else if (mode === "caesar-dec") out = C.caesar(src, -Number(key) || 0);
    else if (mode === "vig-enc") out = C.vigenere(src, key, false);
    else if (mode === "vig-dec") out = C.vigenere(src, key, true);
    else if (mode === "a1-to") out = C.a1z26(src, "to");
    else if (mode === "a1-from") out = C.a1z26(src, "from");
    setText("c-out", out);
    drawFreq(C.freq(out));
  }

  function drawFreq(pairs) {
    const box = $("c-freq");
    if (!box) return;
    const map = {};
    pairs.forEach(function (p) {
      map[p[0]] = p[1];
    });
    const max = pairs.length ? pairs[0][1] : 1;
    box.innerHTML = LETTERS.map(function (L) {
      const n = map[L] || 0;
      const h = max ? Math.max(n ? 4 : 2, Math.round((n / max) * 60)) : 2;
      return "<i style=\"height:" + h + "px\" title=\"" + L + " " + n + "\"></i>";
    }).join("");
  }

  function applyBook() {
    const C = window.INSTAR_CIPHERS;
    if (!C) return;
    const text = val("b-text");
    const coords = val("b-co");
    const out = C.book(text, coords);
    setText("b-out", out);
    renderBookLines(text, coords);
  }

  function renderBookLines(text, coords) {
    const box = $("b-lines");
    if (!box) return;
    const hits = {};
    String(coords || "")
      .trim()
      .split(/\s+/)
      .forEach(function (tok) {
        const m = tok.match(/^(\d+):(\d+)$/);
        if (m) hits[Number(m[1])] = Number(m[2]);
      });
    const lines = String(text || "").split(/\r?\n/);
    const start = Math.max(0, (Object.keys(hits)[0] || 1) - 4);
    const slice = lines.slice(0, 80);
    box.innerHTML = slice
      .map(function (line, i) {
        const n = i + 1;
        const words = line.split(/\s+/);
        const wi = hits[n];
        const body = words
          .map(function (w, j) {
            if (wi && j + 1 === wi) return '<span class="hit">' + escapeHtml(w) + "</span>";
            return escapeHtml(w);
          })
          .join(" ");
        return "<div>" + n + " " + body + "</div>";
      })
      .join("");
    if (start > 0 && box.children[start]) box.children[start].scrollIntoView({ block: "nearest" });
  }

  function applyRunes() {
    const R = window.INSTAR_RUNES;
    if (!R) return;
    const src = val("u-in");
    const dir = val("u-dir") || "sound";
    const out = dir === "carve" ? R.encode(src) : R.decode(src);
    setText("u-out", out);
  }

  async function applyHash() {
    if (!window.INSTAR) return;
    setText("h-out", await INSTAR.sha256(val("h-in")));
    setText("h-norm", INSTAR.norm(val("h-in")) || "(empty after normalize)");
  }

  function rsaSteps() {
    const R = window.INSTAR_RSA;
    if (!R) return;
    const n = val("r-n");
    const e = val("r-e");
    const box = $("r-proof");
    function step(id, on, text) {
      const el = box.querySelector('[data-step="' + id + '"]');
      if (!el) return;
      el.textContent = text;
      el.classList.toggle("on", !!on);
      el.classList.toggle("ok", id === "plain" && !!on);
    }
    step("n", true, "n = " + n);
    const fac = R.factor(n);
    if (!fac) {
      step("pq", true, "no small factors");
      step("phi", false, "phi");
      step("d", false, "d");
      step("plain", false, "plaintext");
      setText("r-out", "no small factors");
      return;
    }
    const phi = (fac[0] - 1) * (fac[1] - 1);
    const d = R.modinv(e, phi);
    step("pq", true, "p = " + fac[0] + "   q = " + fac[1]);
    step("phi", true, "phi = (p-1)(q-1) = " + phi);
    step("d", true, "d = e^-1 mod phi = " + d);
    const cs = val("r-c")
      .split(",")
      .map(function (x) {
        return Number(x.trim());
      })
      .filter(function (x) {
        return !Number.isNaN(x);
      });
    const ms = cs.map(function (c) {
      return R.decryptBlock(c, d, n);
    });
    const word = ms
      .map(function (m) {
        return m >= 32 && m < 127 ? String.fromCharCode(m) : "?";
      })
      .join("");
    step("plain", true, "m = [" + ms.join(", ") + "]  ->  " + word);
    setText("r-out", word);
    pushHist("rsa", word);
  }

  function rsaForge() {
    const R = window.INSTAR_RSA;
    if (!R) return;
    const p = Number(val("r-p"));
    const q = Number(val("r-q"));
    const msg = val("r-msg");
    if (!p || !q) {
      setText("r-forge", "choose two small primes");
      return;
    }
    const n = p * q;
    const phi = (p - 1) * (q - 1);
    let e = 17;
    if (phi % e === 0) e = 3;
    const d = R.modinv(e, phi);
    const cs = msg.split("").map(function (ch) {
      return R.modexp(ch.charCodeAt(0), e, n);
    });
    setText(
      "r-forge",
      "n=" + n + " e=" + e + " d=" + d + "\nc=[" + cs.join(", ") + "]"
    );
  }

  function bindDrop(zoneId, inputId, onFile) {
    const zone = $(zoneId);
    const input = $(inputId);
    if (!zone || !input) return;
    zone.addEventListener("click", function () {
      input.click();
    });
    zone.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        input.click();
      }
    });
    ["dragenter", "dragover"].forEach(function (ev) {
      zone.addEventListener(ev, function (e) {
        e.preventDefault();
        zone.classList.add("is-over");
      });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      zone.addEventListener(ev, function (e) {
        e.preventDefault();
        zone.classList.remove("is-over");
      });
    });
    zone.addEventListener("drop", function (e) {
      const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (!f) return;
      const dt = new DataTransfer();
      dt.items.add(f);
      input.files = dt.files;
      if (onFile) onFile(f);
    });
    input.addEventListener("change", function () {
      if (input.files[0] && onFile) onFile(input.files[0]);
    });
  }

  function currentFile(id) {
    const el = $(id);
    return el && el.files && el.files[0];
  }

  async function runStego(kind) {
    const f = currentFile("s-file");
    if (!f) {
      setText("s-out", "no file");
      return;
    }
    if (kind === "lsb") {
      const t = await INSTAR_STEGO.lsbExtract(f);
      setText("s-out", t || "(no null-terminated UTF-8 in red LSB)");
      pushHist("lsb", t);
    } else {
      const found = await INSTAR_STEGO.stringsDump(f, Number(val("s-min")) || 8);
      setText("s-out", found.join("\n") || "(no strings)");
      pushHist("strings", found[0] || "");
    }
  }

  async function runPlane() {
    const f = currentFile("s-file");
    if (!f) return;
    await INSTAR_STEGO.drawBitPlane(f, $("s-plane"), val("s-ch"), val("s-bit"));
  }

  async function runSpec(file) {
    const f = file || currentFile("p-file");
    if (!f) return;
    await INSTAR_SPEC.drawFile(f, $("p-can"), specOpts());
    pushHist("spec", f.name);
  }

  function bindTabs() {
    const tabs = document.querySelectorAll("#tabs [role='tab']");
    tabs.forEach(function (btn, i) {
      btn.addEventListener("click", function () {
        selectTool(btn.dataset.tab);
      });
      btn.addEventListener("keydown", function (e) {
        let next = i;
        if (e.key === "ArrowDown" || e.key === "ArrowRight") next = (i + 1) % tabs.length;
        else if (e.key === "ArrowUp" || e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
        else if (e.key === "Home") next = 0;
        else if (e.key === "End") next = tabs.length - 1;
        else return;
        e.preventDefault();
        selectTool(tabs[next].dataset.tab);
        tabs[next].focus();
      });
    });
  }

  function typingTarget(el) {
    if (!el) return false;
    const tag = (el.tagName || "").toLowerCase();
    return tag === "input" || tag === "textarea" || tag === "select" || el.isContentEditable;
  }

  function bindKeys() {
    document.addEventListener("keydown", function (e) {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "?" || (e.key === "/" && e.shiftKey)) {
        if (typingTarget(e.target) && e.key !== "?") return;
        const open = document.querySelector(".panel:not([hidden]) .why");
        if (open) {
          e.preventDefault();
          open.open = !open.open;
        }
        return;
      }
      if (typingTarget(e.target)) return;
      if (e.key === "/") {
        e.preventDefault();
        const panel = document.querySelector(".panel:not([hidden])");
        const field = panel && panel.querySelector("textarea, input[type='text']");
        if (field) field.focus();
        return;
      }
      if (e.key >= "1" && e.key <= "7") {
        selectTool(TOOLS[Number(e.key) - 1]);
      }
    });
  }

  function bindPresets() {
    $("c-preset").addEventListener("change", function () {
      const v = $("c-preset").value;
      if (v === "atbash") {
        $("c-in").value = "GSV URIHG TZGV RH MBNKSVW";
        $("c-mode").value = "atbash";
      } else if (v === "rot13") {
        $("c-in").value = "URYYB";
        $("c-mode").value = "rot13";
      } else if (v === "caesar") {
        $("c-in").value = "KHOOR";
        $("c-key").value = "3";
        $("c-mode").value = "caesar-dec";
      } else if (v === "vig") {
        $("c-in").value = "LXFOPVEFRNHR";
        $("c-key").value = "LEMON";
        $("c-mode").value = "vig-dec";
      } else if (v === "nymph") {
        $("c-in").value = (window.INSTAR_PUZZLE && INSTAR_PUZZLE.vigenereCipher) || "";
        $("c-key").value = (window.INSTAR_PUZZLE && INSTAR_PUZZLE.vigenereHint) || "";
        $("c-mode").value = "vig-dec";
      }
      applyClassical();
    });
  }

  async function fetchJournal() {
    const text = await (await fetch("/library/soil-journal.txt")).text();
    $("b-text").value = text;
    if (!$("b-co").value && window.INSTAR_PUZZLE) {
      $("b-co").value = (INSTAR_PUZZLE.bookCoords || []).join(" ");
    }
    applyBook();
  }

  function boot() {
    INSTAR.mountChrome("workbench");
    INSTAR.mountFoot();
    bindTabs();
    bindKeys();
    bindPresets();

    ["c-in", "c-key", "c-mode"].forEach(function (id) {
      $(id).addEventListener("input", applyClassical);
      $(id).addEventListener("change", applyClassical);
    });
    $("c-export").addEventListener("click", function () {
      exportText("instar-classical.txt", $("c-out").textContent);
    });

    $("b-fetch").addEventListener("click", fetchJournal);
    $("b-co").addEventListener("input", applyBook);
    $("b-text").addEventListener("input", applyBook);
    $("b-go").addEventListener("click", function () {
      applyBook();
      pushHist("book", $("b-out").textContent);
    });

    bindDrop("s-drop", "s-file", function () {
      runPlane();
    });
    $("s-lsb").addEventListener("click", function () {
      runStego("lsb");
    });
    $("s-str").addEventListener("click", function () {
      runStego("str");
    });
    $("s-ch").addEventListener("change", runPlane);
    $("s-bit").addEventListener("change", runPlane);

    bindDrop("p-drop", "p-file", function (f) {
      runSpec(f);
    });
    $("p-go").addEventListener("click", function () {
      runSpec();
    });
    $("p-sample").addEventListener("click", async function () {
      const res = await fetch("/media/emergence.wav");
      const blob = await res.blob();
      const f = new File([blob], "emergence.wav");
      const dt = new DataTransfer();
      dt.items.add(f);
      $("p-file").files = dt.files;
      await runSpec(f);
    });
    ["p-nfft", "p-hop", "p-gain"].forEach(function (id) {
      $(id).addEventListener("change", function () {
        if (currentFile("p-file")) runSpec();
      });
    });

    $("r-go").addEventListener("click", rsaSteps);
    $("r-forge-go").addEventListener("click", rsaForge);
    if (window.INSTAR_PUZZLE && INSTAR_PUZZLE.rsa) {
      $("r-n").value = INSTAR_PUZZLE.rsa.n;
      $("r-e").value = INSTAR_PUZZLE.rsa.e;
      $("r-c").value = INSTAR_PUZZLE.rsa.c.join(", ");
    }

    $("u-in").addEventListener("input", applyRunes);
    $("u-dir").addEventListener("change", applyRunes);
    $("u-go").addEventListener("click", function () {
      applyRunes();
      pushHist("runes", $("u-out").textContent);
    });

    $("h-in").addEventListener("input", applyHash);
    $("h-go").addEventListener("click", applyHash);

    const hash = (location.hash || "").replace("#", "");
    selectTool(TOOLS.indexOf(hash) >= 0 ? hash : "classical", true);
    applyClassical();
    if (!reduced()) {
      /* live lab is already wired; no extra motion */
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
