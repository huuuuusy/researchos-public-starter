"""Messages of the read-only vault check in build_public_starter_data.py, in the vault's language."""

VAULT_CHECK_TEXT = {
    "en": {
        "counts": "Your vault: {records} card(s) read, {assets} shown in the Dashboard.",
        "dry": "Nothing was written. To refresh the Dashboard's view of your vault, run this again with --write (it writes {output}, which Git ignores).",
        "wrote": "Wrote {output} (ignored by Git); the Dashboard in personal-vault mode now shows your vault.",
        "found": "Vault check ({n}):",
        "clean": "Vault check: no problems found.",
        "link": "{card}: links to {target}, which does not exist",
        "sensitivity": "{card}: sensitivity is {value!r}; use public, internal, sensitive or private (ros context packs no other value)",
        "summary": "{card}: the Agent Summary is empty; an assistant reads it first",
        "comment": "{card}: line {line!r} ends with a # comment, which is read as part of the value",
        "stale": "{card}: last checked {checked}, but {source} changed on {updated}; check the summary again",
        "original": "{card}: the original at {path} was not found on this computer (a reminder only)",
        "duplicate": "attention schedule: {key} has more than one entry; only the first counts, so keep one",
    },
    "zh-CN": {
        "counts": "你的库：读到 {records} 张卡，其中 {assets} 张会在 Dashboard 里显示。",
        "dry": "没有写入任何文件。想刷新 Dashboard 里你的库，加上 --write 再运行一次（它写 {output}，Git 会忽略这个文件）。",
        "wrote": "已写入 {output}（Git 会忽略）；个人库模式的 Dashboard 现在显示你的库。",
        "found": "库体检（{n} 处）：",
        "clean": "库体检：没有发现问题。",
        "link": "{card}：链接到 {target}，这个文件不存在",
        "sensitivity": "{card}：sensitivity 写的是 {value!r}，请用 public、internal、sensitive 或 private（其他值 ros context 一律不打包）",
        "summary": "{card}：Agent Summary 是空的；助手最先读的就是这一段",
        "comment": "{card}：{line!r} 行尾有 # 注释，会被当成值的一部分",
        "stale": "{card}：上次核对是 {checked}，但 {source} 在 {updated} 改过；请重新核对这份摘要",
        "original": "{card}：本机找不到原件 {path}（只是提醒）",
        "duplicate": "注意力安排：{key} 有不止一段条目，只有第一段算数，请只留一段",
    },
}
