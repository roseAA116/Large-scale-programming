import { spawn } from "node:child_process";
import http from "node:http";
import process from "node:process";

const port = process.env.E2E_PORT ?? "5174";
const baseURL = `http://127.0.0.1:${port}`;

const vite = spawnCommand("npx vite --host 127.0.0.1 --port " + port + " --strictPort");

let exitCode = 1;

try {
  await waitForServer(baseURL);
  exitCode = await runPlaywright(baseURL);
} finally {
  await stopProcess(vite.pid);
}

process.exit(exitCode);

function runPlaywright(url) {
  return new Promise((resolve) => {
    const child = spawnCommand("npx playwright test", {
      env: { ...process.env, E2E_BASE_URL: url }
    });
    child.on("exit", (code) => resolve(code ?? 1));
  });
}

function spawnCommand(command, options = {}) {
  if (process.platform === "win32") {
    return spawn("cmd.exe", ["/d", "/s", "/c", command], {
      ...options,
      stdio: "inherit"
    });
  }
  return spawn(command, {
    ...options,
    shell: true,
    stdio: "inherit"
  });
}

async function waitForServer(url) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < 30_000) {
    if (await canConnect(url)) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`Vite dev server did not start at ${url}`);
}

function canConnect(url) {
  return new Promise((resolve) => {
    const request = http.get(url, (response) => {
      response.resume();
      resolve(response.statusCode !== undefined && response.statusCode < 500);
    });
    request.on("error", () => resolve(false));
    request.setTimeout(1000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

function stopProcess(pid) {
  if (!pid) {
    return Promise.resolve();
  }
  if (process.platform !== "win32") {
    try {
      process.kill(pid, "SIGTERM");
    } catch {
      // Already stopped.
    }
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    const killer = spawn("taskkill", ["/pid", String(pid), "/T", "/F"], {
      stdio: "ignore"
    });
    killer.on("exit", () => resolve());
    killer.on("error", () => resolve());
  });
}
