<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# 配置

保存无凭据 runtime 配置。本仓库固定为 `copy_only` 与 `execution_scope: none`：既不启动本机 Codex 或 Claude Code CLI，也不启用真实 API。报告中的原型或 personal-vault 模式可另外配置受控本地执行，但不得把密钥提交进仓库。

## 示例 Case 开关

`public_starter.case_materials.enabled` 控制公开示例 case 是否进入 active demo data。设为 `false` 时，`08_exports/public_starter/` 文件保留但不再被生成脚本作为 active records 输出。

## Runtime Read 边界

`public-runtime-read-manifest.json` 是公开 preview、source tree 与 copy-only 投影读取的唯一精确文件白名单。manifest 缺失或格式错误，以及条目重复、使用绝对路径、越出仓库、指向符号链接或非普通文件时，边界一律 fail closed。允许一个文件不会连带开放整个目录或同级文件。
