import { chromium } from "playwright";

const base = process.env.INSTAR_URL || "http://localhost:4173";
const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const fails = [];
function ok(name, cond) {
  if (!cond) fails.push(name);
}

await page.goto(base + "/", { waitUntil: "domcontentloaded" });
ok("hello-h1", (await page.locator("h1").innerText()) === "Hello.");
ok("hello-whisper", (await page.locator(".whisper").innerText()).toLowerCase().includes("soil"));
ok("hello-disclaimer", (await page.locator(".disclaimer").innerText()).toLowerCase().includes("not a liber primus solve"));
ok("foot-not-a-solve", (await page.locator(".foot").innerText()).toLowerCase().includes("not a liber primus solve"));
ok("hello-rail-hidden", await page.locator(".molt-rail").count() === 0 || !(await page.locator(".molt-rail").isVisible()));
ok("skins-off", (await page.locator("#skins-btn").getAttribute("aria-pressed")) === "false");

await page.click("#skins-btn");
ok("hello-rail-opt-in", await page.locator(".molt-rail").isVisible());
const namesPainted = await page.evaluate(function () {
  const els = document.querySelectorAll(".molt-rail a, .molt-rail > span");
  return Array.prototype.some.call(els, function (el) {
    const label = el.querySelector(".sr-only, .sr");
    if (!label) return (el.textContent || "").trim().length > 0 && el.getBoundingClientRect().width > 24;
    const r = label.getBoundingClientRect();
    return r.width > 2 && r.height > 2 && r.left >= 0;
  });
});
ok("rail-names-unspoken", !namesPainted);
await page.click("#skins-btn");
ok("hello-rail-hidden-again", await page.locator(".molt-rail").count() === 0 || !(await page.locator(".molt-rail").isVisible()));

await page.goto(base + "/workbench/", { waitUntil: "domcontentloaded" });
ok("workbench-rail-off", await page.locator(".molt-rail").count() === 0 || !(await page.locator(".molt-rail").isVisible()));
await page.waitForSelector("#c-in");
await page.fill("#c-in", "GSV URIHG TZGV RH MBNKSVW");
await page.selectOption("#c-mode", "atbash");
await page.waitForTimeout(50);
const at = await page.locator("#c-out").innerText();
ok("live-atbash", at.includes("THE FIRST GATE"));
ok("freq-bars", (await page.locator("#c-freq i").count()) === 26);

await page.click('[data-tab="book"]');
ok("book-panel", await page.locator("#book").isVisible());
await page.click("#b-fetch");
await page.waitForFunction(() => document.getElementById("b-text").value.length > 20);
ok("journal", (await page.locator("#b-text").inputValue()).length > 20);

await page.click('[data-tab="rsa"]');
await page.click("#r-go");
const proof = await page.locator("#r-proof").innerText();
ok("rsa-steps", proof.includes("p =") && proof.includes("phi"));

await page.goto(base + "/manual/", { waitUntil: "domcontentloaded" });
ok("manual", (await page.locator("h1.stage").innerText()).includes("Field"));
ok("locked-or-open", (await page.locator("article").count()) === 9);

await page.goto(base + "/husk/", { waitUntil: "domcontentloaded" });
ok("husk", (await page.locator("h1.stage").innerText()).toLowerCase().includes("payload"));
await page.click("#run");
const huskOut = await page.locator("#out").innerText();
ok("husk-onion", huskOut.includes("gy3hoy2zizvuzvdb"));
ok("husk-dead", huskOut.toLowerCase().includes("dead"));

await page.goto(base + "/song/", { waitUntil: "domcontentloaded" });
ok("song-fft", await page.locator("#nfft").count() === 1);

await browser.close();
if (fails.length) {
  console.error("VERIFY FAIL", fails.join(","));
  process.exit(1);
}
console.log("VERIFY OK");
