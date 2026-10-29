<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# Dashboard 数据

本目录保存公开 demo 的生成投影。这里的文件不是权威源，而是从虚构 starter 材料生成的可渲染视图。

当前规则：

- `researchos-dashboard.json` 可以展示公开 demo dashboard。
- `generated-public-starter-data.json` 从 `08_exports/public_starter/` 生成，也写在那里。
- 不要把私人 dashboard projection 复制到这里。
- 不要把生成 JSON 当作 confirmed memory。

## Case 模式

`researchos-dashboard.json` 可以继续展示公开 demo。`generated-public-starter-data.json` 则由 `scripts/build_public_starter_data.py` 根据 `public_starter.case_materials.enabled` 生成：开启时包含 case records，关闭时 records 为空，case 文件仅作参考。
