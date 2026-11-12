"""Messages of the read-only vault check in build_public_starter_data.py, in the vault's language."""

VAULT_CHECK_TEXT = {
    "en": {
        "found": "Vault check ({n}):",
        "clean": "Vault check: no problems found.",
        "link": "{card}: links to {target}, which does not exist",
        "sensitivity": "{card}: sensitivity is {value!r}; use public, internal, sensitive or private (ros context packs no other value)",
        "summary": "{card}: the Agent Summary is empty; an assistant reads it first",
        "comment": "{card}: line {line!r} ends with a # comment, which is read as part of the value",
        "stale": "{card}: last checked {checked}, but {source} changed on {updated}; check the summary again",
        "original": "{card}: the original at {path} was not found on this computer (a reminder only)",
    },
    "zh-CN": {
        "found": "库体检（{n} 处）：",
        "clean": "库体检：没有发现问题。",
        "link": "{card}：链接到 {target}，这个文件不存在",
        "sensitivity": "{card}：sensitivity 写的是 {value!r}，请用 public、internal、sensitive 或 private（其他值 ros context 一律不打包）",
        "summary": "{card}：Agent Summary 是空的；助手最先读的就是这一段",
        "comment": "{card}：{line!r} 行尾有 # 注释，会被当成值的一部分",
        "stale": "{card}：上次核对是 {checked}，但 {source} 在 {updated} 改过；请重新核对这份摘要",
        "original": "{card}：本机找不到原件 {path}（只是提醒）",
    },
}
