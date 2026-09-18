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
(function progress() {
  const store = Object.create(null);
  const pctx = {
    window: {},
    document: {
      readyState: "complete",
      documentElement: { setAttribute: function () {}, getAttribute: function () { return ""; } },
      body: {
        classList: { toggle: function () {} },
        setAttribute: function () {},
        getAttribute: function () { return ""; },
        appendChild: function () {},
        insertBefore: function () {},
        firstChild: null,
      },
      addEventListener: function () {},
      querySelector: function () { return null; },
      querySelectorAll: function () { return []; },
      getElementById: function () { return null; },
      createElement: function () { return { setAttribute: function () {}, appendChild: function () {} }; },
    },
    location: { hash: "", hostname: "localhost", protocol: "http:" },
    history: { replaceState: function () {} },
    matchMedia: function () { return { matches: false }; },
    localStorage: {
      getItem: function (k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
      setItem: function (k, v) { store[k] = String(v); },
      removeItem: function (k) { delete store[k]; },
    },
    Uint8Array: Uint8Array,
    TextDecoder: TextDecoder,
    TextEncoder: TextEncoder,
  };
  pctx.window = pctx;
  vm.createContext(pctx);
  vm.runInContext(fs.readFileSync(path.join(root, "core.js"), "utf8"), pctx);
  const I = pctx.window.INSTAR;
  function realPath(href) {
    return typeof href === "string" && href.charAt(0) === "/" && href.indexOf("#") === -1;
  }
  ok("core-boot", !!I && typeof I.resume === "function" && typeof I.complete === "function");
  ok("next-hello", I.nextId() === "hello");
  const fresh = I.resume();
  ok("resume-fresh", fresh.show === false && fresh.href === "/" && realPath(fresh.href));
  I.mark("hello");
  ok("next-nymph", I.nextId() === "nymph");
  const afterHello = I.resume();
  ok("resume-hello-only", afterHello.show === false && I.depth() === 1 && afterHello.href === "/nymph/" && realPath(afterHello.href));
  ok("hint-nymph", I.nextHint() === "A volume waits. Count from one.");
  I.mark("nymph");
  const mid = I.resume();
  ok("resume-soil", mid.show === true && mid.href === "/soil/" && mid.label === "Continue the molt" && realPath(mid.href));
  I.mark("soil");
  ok("resume-tunnel", I.resume().show === true && I.resume().href === "/tunnel/");
  I.mark("tunnel");
  ok("resume-song", I.resume().show === true && I.resume().href === "/song/");
  I.mark("song");
  ok("resume-prime", I.resume().show === true && I.resume().href === "/prime/");
  I.mark("prime");
  ok("resume-liber", I.resume().show === true && I.resume().href === "/liber/");
  I.mark("liber");
  ok("resume-emerge", I.resume().show === true && I.resume().href === "/emerge/");
  I.ORDER.forEach(function (id) { I.mark(id); });
  const done = I.resume();
  ok("resume-complete", I.complete() === true && done.show === false && done.href === "/manual/" && realPath(done.href));
  ok("nextid-done", I.nextId() === null);
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
  ok("hello-continue", hello.indexOf('id="continue-molt"') !== -1 && hello.indexOf("Continue the molt") !== -1);
  ok("hello-mount-continue", hello.indexOf("INSTAR.mountContinue()") !== -1);
  ok("hello-no-nymph-href", !/id="continue-link"[^>]*href="\/nymph\//.test(hello));
  ok("core-paths", core.indexOf("nymph: \"/nymph/\"") !== -1);
  ok("core-resume-real-path", core.indexOf('href || "#"') === -1 && core.indexOf("function resume()") !== -1);
  ok("llms-not-a-solve", banner.test(llms));
  const ver = (llms.match(/^[\-\*]\s*Version:\s*(\S+)\s*$/m) || [])[1];
  ok("llms-version", !!ver);
  ok("puzzle-version", !!ver && puzzle.indexOf('"v": "' + ver + '"') !== -1);
  ok("sw-version", !!ver && sw.indexOf('CACHE = "instar-' + ver + '"') !== -1);
  ["nymph", "soil", "tunnel", "song", "prime", "liber", "emerge"].forEach(function (slug) {
    const html = fs.readFileSync(path.join(pub, slug, "index.html"), "utf8");
    ok(slug + "-live", /id="status"[^>]*aria-live="polite"/.test(html));
  });
})();
(function stringsLong() {
  const len = 70000;
  const bytes = new Array(len).fill(65);
  const s = S.bytesToAscii(bytes);
  ok("strings-long", s.length === len && s.charCodeAt(0) === 65 && s.charCodeAt(len - 1) === 65);
})();
(function rsaFactorFloor() {
  ok("rsa-fac-2", A.factor(2) === null);
  ok("rsa-fac-0", A.factor(0) === null);
  ok("rsa-fac-3", A.factor(3) === null);
  ok("rsa-fac-4", JSON.stringify(A.factor(4)) === "[2,2]");
  ok("rsa-fac-nan", A.factor(NaN) === null);
})();
if (fails.length) {
  console.error("FAIL", fails.join(","));
  process.exit(1);
}
console.log("UNIT OK");
