// helper/scrape_tokopedia_browser.mjs
// Scrape hasil pencarian Tokopedia memakai browser (Playwright + Edge).
// Endpoint GraphQL Tokopedia memblokir klien non-browser dan browser headless,
// jadi kita buka halaman pencarian di jendela Edge sungguhan lalu menangkap
// respons GraphQL `SearchProductV5Query` (hasil organik, tanpa iklan).
//
// Jalankan (dari folder revoshop-backend):
//   node helper/scrape_tokopedia_browser.mjs "laptop,handphone,smart tv" 1 elektronik
//   argumen: keyword (pisah koma), jumlah halaman per keyword, nama output
//
// Output: helper/data/tokopedia_<nama>_capture.json
//   [{ keyword, url, body }]  -> body = respons GraphQL mentah

import { createRequire } from "node:module";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
// Playwright terpasang di node_modules frontend.
const require = createRequire(resolve(here, "../../revoshop-frontend/package.json"));
const { chromium } = require("playwright");

const keywords = (process.argv[2] || "laptop").split(",").map((k) => k.trim()).filter(Boolean);
const pages = Number(process.argv[3] || 1);
const outName = process.argv[4] || keywords[0].toLowerCase().replace(/[^a-z0-9]+/g, "_");

const captured = [];
let currentKeyword = null;

// Headless diblokir proteksi bot Tokopedia (ERR_HTTP2_PROTOCOL_ERROR),
// jadi pakai jendela Edge sungguhan.
const browser = await chromium.launch({
  channel: "msedge",
  headless: false,
  args: ["--disable-blink-features=AutomationControlled"],
});
const context = await browser.newContext({
  locale: "id-ID",
  viewport: { width: 1366, height: 900 },
});
const page = await context.newPage();

page.on("response", async (res) => {
  const url = res.url();
  if (!url.includes("gql.tokopedia.com/graphql/SearchProductV5Query")) return;
  const keyword = currentKeyword;
  try {
    const body = await res.json();
    captured.push({ keyword, url, body });
    console.log(`  [${keyword}] captured SearchProductV5Query (${JSON.stringify(body).length} bytes)`);
  } catch (e) {
    console.log(`  ! [${keyword}] gagal parse respons: ${e.message}`);
  }
});

for (const keyword of keywords) {
  currentKeyword = keyword;
  for (let p = 1; p <= pages; p++) {
    const url = `https://www.tokopedia.com/search?st=product&q=${encodeURIComponent(keyword)}&page=${p}`;
    console.log(`${keyword} page ${p}: ${url}`);
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    // scroll bertahap supaya lazy-load produk terpicu
    for (let i = 0; i < 12; i++) {
      await page.mouse.wheel(0, 1200);
      await page.waitForTimeout(700);
    }
    await page.waitForTimeout(2500);
  }
}

await browser.close();

const outDir = join(here, "data");
mkdirSync(outDir, { recursive: true });
const out = join(outDir, `tokopedia_${outName}_capture.json`);
writeFileSync(out, JSON.stringify(captured, null, 2), "utf-8");
console.log(`saved ${captured.length} responses -> ${out}`);
