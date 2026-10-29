/* ResearchOS maintenance header.
 * 中文：验证 dashboard 请求认证仅作用于同源写请求，并能在服务重启后刷新令牌。
 * English: Verifies dashboard request auth stays same-origin and refreshes tokens after a server restart.
 */

"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const calls = [];
let sessionLoads = 0;

async function fakeFetch(input, init = {}) {
  const url = typeof input === "string" ? input : input.url;
  if (url === "/session-config") {
    sessionLoads += 1;
    const token = sessionLoads === 1 ? "old-token" : "new-token";
    return { ok: true, status: 200, async json() { return { request_header: "X-ResearchOS-Session", request_token: token }; } };
  }
  const headers = new Headers(init.headers || {});
  calls.push({
    url,
    body: init.body,
    contentType: headers.get("Content-Type"),
    filename: headers.get("X-ResearchOS-Filename"),
    method: init.method || input?.method || "GET",
    token: headers.get("X-ResearchOS-Session"),
  });
  if (url === "/work-session-upload" && headers.get("X-ResearchOS-Session") === "old-token") {
    return { ok: false, status: 403 };
  }
  return { ok: true, status: 200 };
}

const window = {
  fetch: fakeFetch,
  location: { href: "http://127.0.0.1:8878/", origin: "http://127.0.0.1:8878", protocol: "http:" },
};
const source = fs.readFileSync(path.join(__dirname, "..", "dashboard", "src", "services", "request-auth.js"), "utf8");
vm.runInNewContext(source, { Headers, Request, URL, window });

const injectedFetch = async () => ({ ok: true, status: 200 });
assert.equal(window.ResearchOSRequestAuth.resolveFetcher(injectedFetch), injectedFetch);
assert.equal(typeof window.ResearchOSRequestAuth.resolveFetcher(), "function");

(async () => {
  const getResponse = await window.fetch("/read");
  assert.equal(getResponse.status, 200);
  assert.equal(sessionLoads, 0);

  const binaryBody = { name: "fixture.pdf" };
  const uploadResponse = await window.fetch("/work-session-upload", {
    method: "POST",
    headers: {
      "Content-Type": "application/octet-stream",
      "X-ResearchOS-Filename": "fixture.pdf",
    },
    body: binaryBody,
  });
  assert.equal(uploadResponse.status, 200);
  assert.equal(sessionLoads, 2);
  const uploads = calls.filter((call) => call.url === "/work-session-upload");
  assert.deepEqual(uploads.map((call) => call.token), ["old-token", "new-token"]);
  assert.deepEqual(uploads.map((call) => call.contentType), ["application/octet-stream", "application/octet-stream"]);
  assert.deepEqual(uploads.map((call) => call.filename), ["fixture.pdf", "fixture.pdf"]);
  assert.ok(uploads.every((call) => call.body === binaryBody));

  const writeResponse = await window.fetch("/write", { method: "POST", body: "{}" });
  assert.equal(writeResponse.status, 200);
  const write = calls.find((call) => call.url === "/write");
  assert.equal(write.token, "new-token");
  assert.equal(write.contentType, "application/json");
  assert.equal(write.body, "{}");

  await window.fetch("https://example.test/external", { method: "POST", body: "{}" });
  const external = calls.find((call) => call.url === "https://example.test/external");
  assert.equal(external.token, null);

  console.log("Request auth regression passed.");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
