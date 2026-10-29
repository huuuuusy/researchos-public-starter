/* ResearchOS maintenance header.
 * 中文：验证 work-session-client 的六个本地请求：HTTP 的 ok/status 不会被服务端返回体里的同名字段覆盖。
 * English: Verifies the six work-session-client requests keep the HTTP ok/status even when the server body reuses those field names.
 */

"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const context = { window: {} };
vm.createContext(context);
for (const file of ["dashboard/src/services/request-auth.js", "dashboard/src/services/work-session-client.js"]) {
  vm.runInContext(fs.readFileSync(path.join(root, file), "utf8"), context);
}
const Client = context.window.ResearchOSWorkSessionClient;

const requests = {
  uploadSourceFile: (deps) => Client.uploadSourceFile({ name: "source.pdf" }, deps),
  completePortfolioItem: (deps) => Client.completePortfolioItem({ itemId: "item-1" }, {}, deps),
  setPortfolioState: (deps) => Client.setPortfolioState({ id: "item-1", state: "queued" }, "mainline", {}, deps),
  applyAttentionAction: (deps) => Client.applyAttentionAction({ providerId: "portfolio", id: "item-1" }, { action: "today" }, deps),
  undoMutation: (deps) => Client.undoMutation({ token: "undo-1", kind: "attention" }, deps),
  openLocalFile: (deps) => Client.openLocalFile("notes/source.md", deps),
};

function fetcherReturning(response, calls) {
  return async (url, init) => {
    calls.push({ url, init });
    return response;
  };
}

(async () => {
  for (const [name, request] of Object.entries(requests)) {
    // A failed HTTP response whose body claims success keeps the HTTP verdict and status.
    let calls = [];
    const failed = await request({ fetcher: fetcherReturning({ ok: false, status: 500, json: async () => ({ ok: true, status: "done", message: "body" }) }, calls) });
    assert.equal(calls.length, 1, `${name} must send one request`);
    assert.equal(calls[0].init.cache, "no-store", `${name} must bypass the HTTP cache`);
    assert.equal(failed.ok, false, `${name}: server body must not turn an HTTP failure into success`);
    assert.equal(failed.status, 500, `${name}: status must be the HTTP status, not a body field`);
    assert.equal(failed.message, "body", `${name}: other body fields stay available`);

    // A successful HTTP response still needs the body to confirm success.
    calls = [];
    const succeeded = await request({ fetcher: fetcherReturning({ ok: true, status: 200, json: async () => ({ ok: true, status: "queued" }) }, calls) });
    assert.equal(succeeded.ok, true, `${name}: HTTP 200 with ok body succeeds`);
    assert.equal(succeeded.status, 200, `${name}: status stays numeric`);

    calls = [];
    const unconfirmed = await request({ fetcher: fetcherReturning({ ok: true, status: 200, json: async () => { throw new Error("not json"); } }, calls) });
    assert.equal(unconfirmed.ok, false, `${name}: an unreadable body is not success`);
    assert.equal(unconfirmed.status, 200, `${name}: unreadable body keeps the HTTP status`);

    const thrown = await request({ fetcher: async () => { throw new Error("offline"); } });
    assert.equal(thrown.ok, false, `${name}: a network error is reported as failure`);
    assert.equal(thrown.message, "offline", `${name}: the network error message is kept`);
  }
  console.log("work-session client request results keep the HTTP ok/status");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
