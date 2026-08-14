#!/usr/bin/env node
/* Responsive runtime gate for the generated GitHub Pages site. */

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const base = process.env.SITE_AUDIT_BASE || "http://127.0.0.1:8765/";
const manifest = JSON.parse(fs.readFileSync(path.join(root, "data/site-manifest.json"), "utf8"));
const out = path.join(root, "tmp", "site-visual-audit");
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });

const allPages = Object.keys(manifest.pages).sort();
const samples = [
  "index.html",
  "parity.html",
  "modules/72565.html",
  "modules/72572.html",
  "lessons/2633987.html",
  "lessons/2634012.html",
  "lessons/2634035.html",
  "lessons/2634037.html",
  "lessons/2634055.html",
  "lessons/2634354.html"
].filter((value) => allPages.includes(value));

const browser = await chromium.launch({ headless: true });
const failures = [];
const metrics = [];

async function inspect(relative, viewport, screenshot = false) {
  const page = await browser.newPage({ viewportSize: viewport });
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.hostname === "127.0.0.1") await route.continue(); else await route.abort();
  });
  try {
    const response = await page.goto(new URL(relative, base).href, { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!response || !response.ok()) failures.push(`${relative} returned ${response ? response.status() : "no response"}`);
    await page.waitForLoadState("load", { timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(80);
    const result = await page.evaluate(() => {
      const root = document.documentElement;
      const brokenImages = Array.from(document.images)
        .filter((img) => {
          if (!img.currentSrc) return false;
          const url = new URL(img.currentSrc, location.href);
          return url.hostname === location.hostname && img.naturalWidth === 0;
        })
        .map((img) => img.currentSrc);
      const emptyLinks = Array.from(document.querySelectorAll("a[href='#'], a:not([href])"))
        .map((a) => (a.textContent || "").trim().slice(0, 80));
      const overflow = root.scrollWidth - root.clientWidth;
      return { title: document.title, overflow, brokenImages, emptyLinks, width: root.clientWidth, scrollWidth: root.scrollWidth };
    });
    metrics.push({ page: relative, viewport: viewport.width, ...result });
    if (result.overflow > 1) failures.push(`${relative} overflows ${viewport.width}px viewport by ${result.overflow}px`);
    if (result.brokenImages.length) failures.push(`${relative} has broken local images: ${result.brokenImages.join(", ")}`);
    if (result.emptyLinks.length) failures.push(`${relative} has empty links: ${result.emptyLinks.join(" | ")}`);

    const tabGroups = await page.locator(".enhanceable_content.tabs").count();
    if (tabGroups) {
      await page.waitForFunction(() =>
        Array.from(document.querySelectorAll(".enhanceable_content.tabs > ul:first-child a[href^='#']"))
          .some((link) => link.hasAttribute("aria-selected")),
        null,
        { timeout: 10000 }
      );
      const group = page.locator(".enhanceable_content.tabs").first();
      const links = group.locator(":scope > ul:first-child a[href^='#']");
      if (await links.count() > 1) {
        const second = links.nth(1);
        await second.click();
        if ((await second.getAttribute("aria-selected")) !== "true") failures.push(`${relative} tab controls did not activate`);
      }
    }
    if (screenshot) {
      const name = relative.replace(/[/.]/g, "-");
      await page.screenshot({ path: path.join(out, `${name}-${viewport.width}.png`), fullPage: true });
    }
  } catch (error) {
    failures.push(`${relative} runtime error: ${error.message}`);
  } finally {
    await page.close();
  }
}

async function pool(values, worker, count = 6) {
  let index = 0;
  async function next() {
    while (index < values.length) {
      const current = values[index++];
      await worker(current);
    }
  }
  await Promise.all(Array.from({ length: count }, next));
}

await pool(allPages, (relative) => inspect(relative, { width: 390, height: 844 }, false), 3);
for (const relative of samples) {
  await inspect(relative, { width: 1280, height: 900 }, true);
  await inspect(relative, { width: 390, height: 844 }, true);
}

await browser.close();
fs.writeFileSync(path.join(out, "metrics.json"), JSON.stringify(metrics, null, 2) + "\n");
fs.writeFileSync(path.join(out, "failures.json"), JSON.stringify(failures, null, 2) + "\n");
console.log(JSON.stringify({ status: failures.length ? "FAIL" : "PASS", pagesAt390: allPages.length, screenshots: samples.length * 2, failures }, null, 2));
if (failures.length) process.exit(1);
