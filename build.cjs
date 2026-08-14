#!/usr/bin/env node
// Compatibility entrypoint. The maintained builder is Python and dependency-free.
const { spawnSync } = require("node:child_process");
const path = require("node:path");
const result = spawnSync("python3", [path.join(__dirname, "scripts", "build_site.py")], {
  cwd: __dirname,
  stdio: "inherit",
});
process.exit(result.status ?? 1);
