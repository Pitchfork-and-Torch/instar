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
};
ctx.window = ctx;
vm.createContext(ctx);
["ciphers.js", "runes.js", "rsa.js"].forEach(function (f) {
  vm.runInContext(fs.readFileSync(path.join(root, f), "utf8"), ctx);
});
const C = ctx.window.INSTAR_CIPHERS;
const R = ctx.window.INSTAR_RUNES;
const A = ctx.window.INSTAR_RSA;
const fails = [];
function ok(name, cond) {
  if (!cond) fails.push(name);
}
ok("atbash", C.atbash("GSV URIHG TZGV RH MBNKSVW") === "THE FIRST GATE IS NYMPHED");
ok("rot13", C.rot13("URYYB") === "HELLO");
ok("caesar", C.caesar("KHOOR", -3) === "HELLO");
ok("vig", C.vigenere("LXFOPVEFRNHR", "LEMON", true) === "ATTACKATDAWN");
ok("book", C.book("alpha\nbeta gamma\n", "2:2") === "gamma");
ok("freq", C.freq("AAAABB")[0][0] === "A");
ok("rune-round", R.decode(R.encode("EMERGE")) === "EMERGE");
ok("rsa-fac", JSON.stringify(A.factor(3139)) === "[43,73]");
if (fails.length) {
  console.error("FAIL", fails.join(","));
  process.exit(1);
}
console.log("UNIT OK");
