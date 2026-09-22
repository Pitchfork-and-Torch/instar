import { spawn } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const pub = path.join(here, "..", "public");
const port = Number(process.env.INSTAR_PORT || 4173);
let base = process.env.INSTAR_URL || "";
let child = null;

function waitPort(p, ms) {
  const deadline = Date.now() + ms;
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const sock = net.connect({ port: p, host: "127.0.0.1" }, () => {
        sock.end();
        resolve();
      });
      sock.on("error", () => {
        sock.destroy();
        if (Date.now() > deadline) reject(new Error("static server timeout"));
        else setTimeout(attempt, 150);
      });
    };
    attempt();
  });
}

function killServer() {
  if (!child || !child.pid) return;
  if (process.platform === "win32") {
    spawn("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
      stdio: "ignore",
      shell: true,
    });
  } else {
    child.kill("SIGTERM");
  }
}

if (!base) {
  child = spawn("py", ["-3", "-m", "http.server", String(port), "--bind", "127.0.0.1"], {
    cwd: pub,
    stdio: "ignore",
    shell: true,
  });
  process.on("exit", killServer);
  await waitPort(port, 20000);
  base = "http://127.0.0.1:" + port;
}

function chromeCandidates() {
  const home = process.env.USERPROFILE || process.env.HOME || "";
  const local = process.env.LOCALAPPDATA || path.join(home, "AppData", "Local");
  const roots = [path.join(local, "ms-playwright")];
  const found = [];
  if (process.env.INSTAR_CHROME) found.push(process.env.INSTAR_CHROME);
  for (const root of roots) {
    try {
      const names = fs.readdirSync(root);
      names
        .filter(function (n) {
          return n.startsWith("chromium-") && !n.includes("headless");
        })
        .sort()
        .reverse()
        .forEach(function (n) {
          found.push(path.join(root, n, "chrome-win64", "chrome.exe"));
          found.push(path.join(root, n, "chrome-linux", "chrome"));
          found.push(path.join(root, n, "chrome-mac", "Chromium.app"));
        });
    } catch {
      /* no cache */
    }
  }
  return found.filter(function (p) {
    try {
      return fs.existsSync(p);
    } catch {
      return false;
    }
  });
}

async function launchBrowser() {
  const args = ["--no-sandbox", "--disable-dev-shm-usage"];
  try {
    return await chromium.launch({ headless: true, args });
  } catch {
    /* bundled revision missing */
  }
  for (const executablePath of chromeCandidates()) {
    try {
      return await chromium.launch({ headless: true, args, executablePath });
    } catch {
      /* try next */
    }
  }
  try {
    return await chromium.launch({ channel: "chrome", headless: true, args });
  } catch (err) {
    throw new Error("no Chromium for verify_lab (do not use Edge): " + err.message);
  }
}

const browser = await launchBrowser();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const fails = [];
function ok(name, cond) {
  if (!cond) fails.push(name);
}

await page.goto(base + "/", { waitUntil: "domcontentloaded" });
ok("hello-h1", (await page.locator("h1").innerText()) === "Hello.");
ok("hello-whisper", (await page.locator(".whisper").innerText()).toLowerCase().includes("soil"));
ok("hello-disclaimer", (await page.locator(".disclaimer").innerText()).toLowerCase().includes("not a liber primus solve"));
await page.waitForFunction(
  () => (document.querySelector(".foot")?.innerText || "").length > 20,
);
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
ok("hello-continue-hidden", await page.locator("#continue-molt").isHidden());

await page.evaluate(function () {
  localStorage.setItem("instar.v1", JSON.stringify({ hello: true, nymph: true }));
});
await page.reload({ waitUntil: "domcontentloaded" });
ok("hello-continue-shown", await page.locator("#continue-molt").isVisible());
ok("hello-continue-soil", (await page.locator("#continue-link").getAttribute("href")) === "/soil/");
ok("hello-continue-label", ((await page.locator("#continue-link").textContent()) || "").trim() === "Continue the molt");
ok(
  "hello-continue-real-path",
  ((await page.locator("#continue-link").getAttribute("href")) || "").charAt(0) === "/" &&
    !((await page.locator("#continue-link").getAttribute("href")) || "").includes("#"),
);
await Promise.all([
  page.waitForURL(function (url) {
    return /\/soil\/?$/.test(url.pathname);
  }),
  page.click("#continue-link"),
]);
ok("hello-continue-lands-soil", /\/soil\/?$/.test(new URL(page.url()).pathname));
await page.goto(base + "/", { waitUntil: "domcontentloaded" });

await page.evaluate(function () {
  localStorage.setItem(
    "instar.v1",
    JSON.stringify({
      hello: true,
      nymph: true,
      soil: true,
      tunnel: true,
      song: true,
      prime: true,
      liber: true,
      emerge: true,
    }),
  );
});
await page.reload({ waitUntil: "domcontentloaded" });
ok("hello-continue-done", await page.locator("#continue-molt").isHidden());
await page.evaluate(function () {
  localStorage.removeItem("instar.v1");
});

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
ok("manual-lock-note", (await page.locator("article.locked h2 .lock-note").count()) > 0);

await page.goto(base + "/husk/", { waitUntil: "domcontentloaded" });
ok("husk", (await page.locator("h1.stage").innerText()).toLowerCase().includes("payload"));
await page.click("#run");
const huskOut = await page.locator("#out").innerText();
ok("husk-onion", huskOut.includes("gy3hoy2zizvuzvdb"));
ok("husk-dead", huskOut.toLowerCase().includes("dead"));

await page.goto(base + "/song/", { waitUntil: "domcontentloaded" });
ok("song-fft", await page.locator("#nfft").count() === 1);

const molt = [
  ["/nymph/", "nymph"],
  ["/soil/", "soil"],
  ["/tunnel/", "tunnel"],
  ["/song/", "song"],
  ["/prime/", "prime"],
  ["/liber/", "liber"],
  ["/emerge/", "emerge"],
  ["/brood/", "brood"],
];
for (const [pathName, slug] of molt) {
  await page.goto(base + pathName, { waitUntil: "domcontentloaded" });
  const skip = page.locator("a.skip");
  ok(slug + "-skip", (await skip.count()) === 1);
  ok(slug + "-skip-href", (await skip.getAttribute("href")) === "#main");
  ok(slug + "-main", (await page.locator("main#main").count()) === 1);
  await skip.focus();
  ok(
    slug + "-skip-on-focus",
    await skip.evaluate(function (el) {
      const r = el.getBoundingClientRect();
      return r.width > 24 && r.height > 12 && r.left >= 0 && r.top >= 0;
    }),
  );
  if ((await page.locator("#status").count()) === 1) {
    ok(slug + "-status-live", (await page.locator("#status").getAttribute("aria-live")) === "polite");
  }
}

await browser.close();
killServer();
if (fails.length) {
  console.error("VERIFY FAIL", fails.join(","));
  process.exit(1);
}
console.log("VERIFY OK");
