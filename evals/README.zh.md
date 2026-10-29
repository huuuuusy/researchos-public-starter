<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# 评估

保存公开安全的验证样例和检查说明。评估应证明边界和流程，而不是暴露非公开数据。

每个测试文件自己把 `scripts/` 加入 `sys.path`，因此任何文件都能单独运行，也能在 `python3 -m unittest discover -s evals` 下以任意顺序运行。内核、适配器与服务端模块到测试的索引见 [README.md](README.md)，由 `python3 evals/test_module_tests.py --write-index` 生成。
