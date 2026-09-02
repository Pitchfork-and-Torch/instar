const fs = require("fs");
const vm = require("vm");
const path = require("path");
const root = path.join(__dirname, "..", "public", "js");
const ctx = {
  window: {},
  document: {
    readyState: "complete",
    addEventListener: function () {},
    querySelector: function () { return null; },
    querySelectorAll: function () { return []; },
    getElementById: function () { return null; },
    createElement: function () { return {}; },
  },
  location: { hash: "", hostname: "localhost", protocol: "http:" },
  history: { replaceState: function () {} },
  matchMedia: function () { return { matches: false }; },
  Uint8Array: Uint8Array,
  TextDecoder: TextDecoder,
};
ctx.window = ctx;
vm.createContext(ctx);
["ciphers.js", "runes.js", "rsa.js", "page56.js", "stego.js"].forEach(function (f) {
  vm.runInContext(fs.readFileSync(path.join(root, f), "utf8"), ctx);
});
const C = ctx.window.INSTAR_CIPHERS;
const R = ctx.window.INSTAR_RUNES;
const A = ctx.window.INSTAR_RSA;
const P = ctx.window.INSTAR_PAGE56;
const S = ctx.window.INSTAR_STEGO;
const fails = [];
function ok(name, cond) {
  if (!cond) fails.push(name);
}
ok("atbash", C.atbash("GSV URIHG TZGV RH MBNKSVW") === "THE FIRST GATE IS NYMPHED");
ok("rot13", C.rot13("URYYB") === "HELLO");
ok("caesar", C.caesar("KHOOR", -3) === "HELLO");
ok("caesar-nan", C.caesar("KHOOR", NaN) === "KHOOR");
ok("caesar-word-key", C.caesar("KHOOR", "TIBERIVS") === "KHOOR");
ok("vig", C.vigenere("LXFOPVEFRNHR", "LEMON", true) === "ATTACKATDAWN");
ok("book", C.book("alpha\nbeta gamma\n", "2:2") === "gamma");
ok("freq", C.freq("AAAABB")[0][0] === "A");
ok("rune-round", R.decode(R.encode("EMERGE")) === "EMERGE");
ok("rsa-fac", JSON.stringify(A.factor(3139)) === "[43,73]");
ok("p56-join", P.LINES.join("") === P.HEX);
ok("p56-extract", P.first8(P.LINES) === "3636776359466b4cd4618dee464fdaf14568926a");
ok("p56-onion", P.onionFromExtract(P.first8(P.LINES)) === P.ONION_V2);
ok("p56-left", P.after8(P.LINES).length === 88);
ok("p56-vt", P.hexBytes(P.HEX)[37] === 0x0b);
ok("p56-wrap8", P.onionFromExtract(P.first8(P.chunks(P.HEX, 16))) !== P.ONION_V2);
ok("p56-wrap4", P.first8(P.chunks(P.HEX, 32)).length === 32);
(function lsbMiss() {
  const bytes = [0x48, 0x49, 0x00];
  const bits = [];
  bytes.forEach(function (b) {
    for (let k = 7; k >= 0; k--) bits.push((b >> k) & 1);
  });
  const data = new Uint8ClampedArray(bits.length * 4);
  for (let i = 0; i < bits.length; i++) {
    if (bits[i]) data[i * 4] |= 1;
    data[i * 4 + 1] |= 8;
    data[i * 4 + 3] = 255;
  }
  ok("lsb-red", S.extractPlane(data, 0, 0) === "HI");
  ok("lsb-green3-miss", S.extractPlane(data, 1, 3) !== "HI");
})();
(function house() {
  const pub = path.join(__dirname, "..", "public");
  const core = fs.readFileSync(path.join(pub, "js", "core.js"), "utf8");
  const hello = fs.readFileSync(path.join(pub, "index.html"), "utf8");
  const llms = fs.readFileSync(path.join(pub, "llms.txt"), "utf8");
  const puzzle = fs.readFileSync(path.join(pub, "js", "puzzle.js"), "utf8");
  const sw = fs.readFileSync(path.join(pub, "sw.js"), "utf8");
  const banner = /not a Liber Primus solve/i;
  ok("foot-not-a-solve", banner.test(core));
  ok("hello-not-a-solve", banner.test(hello));
  ok("llms-not-a-solve", banner.test(llms));
  const ver = (llms.match(/^[\-\*]\s*Version:\s*(\S+)\s*$/m) || [])[1];
  ok("llms-version", !!ver);
  ok("puzzle-version", !!ver && puzzle.indexOf('"v": "' + ver + '"') !== -1);
  ok("sw-version", !!ver && sw.indexOf('CACHE = "instar-' + ver + '"') !== -1);
})();
if (fails.length) {
  console.error("FAIL", fails.join(","));
  process.exit(1);
}
console.log("UNIT OK");
