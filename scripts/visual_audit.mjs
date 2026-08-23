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

// Redirect aliases are verified structurally by verify_site.py. They navigate
// immediately, so treating them as visual pages can destroy the evaluation
// context before the responsive checks run.
const redirectPages = Object.values(manifest.pages).filter((page) => page.kind === "legacy_redirect").length;
const allPages = Object.entries(manifest.pages)
  .filter(([, page]) => page.kind !== "legacy_redirect")
  .map(([relative]) => relative)
  .sort();
const samples = [
  "index.html",
  "about.html",
  "parity.html",
  "modules/72565.html",
  "modules/72572.html",
  "lessons/2633987.html",
  "lessons/2634019.html",
  "lessons/2634012.html",
  "lessons/2634022.html",
  "lessons/2634023.html",
  "lessons/2634030.html",
  "lessons/2634035.html",
  "lessons/2634037.html",
  "lessons/2634055.html",
  "modules/72574.html",
  "lessons/2661807.html",
  "lessons/2661808.html",
  "lessons/2661809.html",
  "lessons/2661810.html",
  "lessons/2661811.html",
  "modules/72580.html",
  "lessons/2634166.html",
  "lessons/2634168.html",
  "lessons/2634173.html",
  "lessons/2634354.html"
].filter((value) => allPages.includes(value));

const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {})
});
const failures = [];
const metrics = [];

async function inspect(relative, viewport, screenshot = false, options = {}) {
  const page = await browser.newPage({ viewport });
  if (options.reducedMotion) await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.hostname === "127.0.0.1") await route.continue(); else await route.abort();
  });
  try {
    const response = await page.goto(new URL(relative, base).href, { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!response || !response.ok()) failures.push(`${relative} returned ${response ? response.status() : "no response"}`);
    await page.waitForLoadState("load", { timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(80);
    if (options.textScale) {
      await page.evaluate((scale) => { document.documentElement.style.fontSize = `${scale * 100}%`; }, options.textScale);
      await page.waitForTimeout(40);
    }
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
      const missingAlt = Array.from(document.images)
        .filter((img) => !img.hasAttribute("alt"))
        .map((img) => img.currentSrc || img.src || "image without src");
      const ids = Array.from(document.querySelectorAll("[id]")).map((node) => node.id);
      const duplicateIds = ids.filter((id, index) => id && ids.indexOf(id) !== index);
      const unlabeledControls = Array.from(document.querySelectorAll("button, input, select, textarea"))
        .filter((control) => {
          if (control.getAttribute("aria-label") || control.getAttribute("aria-labelledby")) return false;
          if (control.id && document.querySelector(`label[for="${CSS.escape(control.id)}"]`)) return false;
          if (control.closest("label")) return false;
          return !(control.tagName === "BUTTON" && (control.textContent || "").trim());
        })
        .map((control) => `${control.tagName.toLowerCase()}#${control.id || "unnamed"}`);
      const overflow = root.scrollWidth - root.clientWidth;
      return {
        title: document.title,
        overflow,
        brokenImages,
        emptyLinks,
        missingAlt,
        duplicateIds: Array.from(new Set(duplicateIds)),
        unlabeledControls,
        hasMain: Boolean(document.getElementById("main-content")),
        hasPageTitle: Boolean(document.querySelector(".page-title")),
        hasPrimaryNav: Boolean(document.querySelector('nav[aria-label="Primary navigation"]')),
        hasSkipLink: Boolean(document.querySelector('.skip-link[href="#main-content"]')),
        runningAnimations: document.getAnimations().filter((animation) => animation.playState === "running").length,
        width: root.clientWidth,
        scrollWidth: root.scrollWidth
      };
    });
    metrics.push({ page: relative, viewport: viewport.width, textScale: options.textScale || 1, reducedMotion: Boolean(options.reducedMotion), ...result });
    if (result.width !== viewport.width) {
      failures.push(`${relative} requested ${viewport.width}px viewport but rendered at ${result.width}px`);
    }
    if (result.overflow > 1) failures.push(`${relative} overflows ${viewport.width}px viewport by ${result.overflow}px`);
    if (result.brokenImages.length) failures.push(`${relative} has broken local images: ${result.brokenImages.join(", ")}`);
    if (result.emptyLinks.length) failures.push(`${relative} has empty links: ${result.emptyLinks.join(" | ")}`);
    if (result.missingAlt.length) failures.push(`${relative} has images without alt attributes: ${result.missingAlt.join(", ")}`);
    if (result.duplicateIds.length) failures.push(`${relative} has duplicate ids: ${result.duplicateIds.join(", ")}`);
    if (result.unlabeledControls.length) failures.push(`${relative} has unlabeled controls: ${result.unlabeledControls.join(", ")}`);
    if (!result.hasMain || !result.hasPageTitle || !result.hasPrimaryNav || !result.hasSkipLink) {
      failures.push(`${relative} is missing required page structure: main=${result.hasMain}, title=${result.hasPageTitle}, nav=${result.hasPrimaryNav}, skip=${result.hasSkipLink}`);
    }
    if (options.reducedMotion && result.runningAnimations) failures.push(`${relative} has ${result.runningAnimations} running animations with reduced motion enabled`);

    if (relative === "index.html") {
      const courseSearch = page.getByLabel("Find a module or lesson", { exact: true });
      await courseSearch.fill("circuits");
      const searchMessage = await page.locator("#search-status").innerText();
      const visibleModules = await page.locator("[data-module]:not([hidden])").count();
      if (!visibleModules || !/match/.test(searchMessage)) failures.push(`index.html search did not return a visible module and status message`);
      await courseSearch.fill("");
    }

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
  await inspect(relative, { width: 390, height: 844 }, false, { textScale: 1.25, reducedMotion: true });
}

await browser.close();
fs.writeFileSync(path.join(out, "metrics.json"), JSON.stringify(metrics, null, 2) + "\n");
fs.writeFileSync(path.join(out, "failures.json"), JSON.stringify(failures, null, 2) + "\n");
console.log(JSON.stringify({ status: failures.length ? "FAIL" : "PASS", pagesAt390: allPages.length, redirectPages, screenshots: samples.length * 2, enlargedTextAndReducedMotionSamples: samples.length, failures }, null, 2));
if (failures.length) process.exit(1);
