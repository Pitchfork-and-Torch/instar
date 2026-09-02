/* Anglo-Saxon futhorc sound values. Not Cicada's Gematria Primus table. */
(function () {
  const MAP = {
    "\u16a0": "F",
    "\u16a2": "U",
    "\u16a3": "Y",
    "\u16a6": "TH",
    "\u16a8": "O",
    "\u16aa": "A",
    "\u16b1": "R",
    "\u16b3": "C",
    "\u16b7": "G",
    "\u16b9": "W",
    "\u16bb": "H",
    "\u16be": "N",
    "\u16c1": "I",
    "\u16c8": "P",
    "\u16ca": "S",
    "\u16cb": "S",
    "\u16cf": "T",
    "\u16d2": "B",
    "\u16d6": "E",
    "\u16d7": "M",
    "\u16da": "L",
    "\u16de": "D",
  };
  const REV = {};
  Object.keys(MAP).forEach(function (k) {
    const v = MAP[k];
    if (!REV[v]) REV[v] = k;
  });
  function decode(s) {
    return String(s || "")
      .split("")
      .map((ch) => (ch === " " || ch === "\n" ? ch : MAP[ch] || ch))
      .join("");
  }
  function encode(s) {
    const u = String(s || "").toUpperCase();
    let i = 0;
    let out = "";
    while (i < u.length) {
      if (u.slice(i, i + 2) === "TH" && REV.TH) {
        out += REV.TH;
        i += 2;
        continue;
      }
      const ch = u[i];
      if (ch === " " || ch === "\n") {
        out += ch;
        i += 1;
        continue;
      }
      out += REV[ch] || ch;
      i += 1;
    }
    return out;
  }
  window.INSTAR_RUNES = { MAP, REV, decode, encode };
})();
