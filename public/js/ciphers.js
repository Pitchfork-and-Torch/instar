/* Classical cipher workbench. */
(function () {
  function lettersOnly(s) {
    return String(s || "");
  }
  function atbash(s) {
    return lettersOnly(s).replace(/[A-Za-z]/g, (ch) => {
      const base = ch <= "Z" ? 65 : 97;
      return String.fromCharCode(base + 25 - (ch.charCodeAt(0) - base));
    });
  }
  function caesar(s, n) {
    n = Number(n);
    if (!Number.isFinite(n)) n = 0;
    n = ((n % 26) + 26) % 26;
    return lettersOnly(s).replace(/[A-Za-z]/g, (ch) => {
      const base = ch <= "Z" ? 65 : 97;
      return String.fromCharCode(base + ((ch.charCodeAt(0) - base + n) % 26));
    });
  }
  function rot13(s) {
    return caesar(s, 13);
  }
  function vigenere(s, key, dec) {
    key = String(key || "")
      .toUpperCase()
      .replace(/[^A-Z]/g, "");
    if (!key) return s;
    let ki = 0;
    return lettersOnly(s).replace(/[A-Za-z]/g, (ch) => {
      const base = ch <= "Z" ? 65 : 97;
      const k = key.charCodeAt(ki % key.length) - 65;
      ki += 1;
      const shift = dec ? (26 - k) : k;
      return String.fromCharCode(base + ((ch.charCodeAt(0) - base + shift) % 26));
    });
  }
  function a1z26(s, mode) {
    if (mode === "to") {
      return String(s || "")
        .toUpperCase()
        .replace(/[A-Z]/g, (ch) => String(ch.charCodeAt(0) - 64) + " ")
        .trim();
    }
    return String(s || "")
      .split(/[^0-9]+/)
      .filter(Boolean)
      .map((n) => {
        const v = Number(n);
        return v >= 1 && v <= 26 ? String.fromCharCode(64 + v) : "";
      })
      .join("");
  }
  function freq(s) {
    const map = {};
    for (const ch of String(s || "").toUpperCase()) {
      if (ch < "A" || ch > "Z") continue;
      map[ch] = (map[ch] || 0) + 1;
    }
    return Object.entries(map).sort((a, b) => b[1] - a[1]);
  }
  function book(text, coords) {
    const lines = String(text || "").split(/\r?\n/);
    return String(coords || "")
      .trim()
      .split(/\s+/)
      .map((tok) => {
        const m = tok.match(/^(\d+):(\d+)$/);
        if (!m) return "?";
        const line = lines[Number(m[1]) - 1] || "";
        const word = line.split(/\s+/)[Number(m[2]) - 1] || "?";
        return word.replace(/[^A-Za-z]/g, "");
      })
      .join(" ");
  }

  window.INSTAR_CIPHERS = { atbash, caesar, rot13, vigenere, a1z26, freq, book };
})();
