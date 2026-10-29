<p align="right">
  <strong>English</strong> | <a href="README.zh.md">中文</a>
</p>

# Dashboard Data

This directory stores generated public demo projections. The files here are not authority; they are renderable views built from fictional starter material.

Current rule:

- `researchos-dashboard.json` may show the public demo dashboard.
- `generated-public-starter-data.json` is generated from `08_exports/public_starter/` and written there.
- Do not copy private dashboard projections into this directory.
- Do not treat generated JSON as confirmed memory.

## Case mode

`researchos-dashboard.json` may keep showing the public demo. `scripts/build_public_starter_data.py` generates `generated-public-starter-data.json` according to `public_starter.case_materials.enabled`: when it is on, the file includes the case records; when it is off, the records are empty and the case files remain as references only.
