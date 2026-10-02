# CodeLens 代码审查 Agent

Python / C++ 单文件代码审查 Agent，使用 Python + Streamlit，可连接 DeepSeek。

## Windows 首次运行

1. 先安装 Python 3.11 或 3.12，并勾选 Add Python to PATH。
2. 将整个压缩包解压到一个目录，不要直接在压缩包内运行。
3. 在解压后的 CodeLens 文件夹打开 PowerShell，执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

首次安装需要网络。安装完成后双击 `start.cmd`，打开终端显示的本地地址（通常 http://127.0.0.1:8501）。若端口被占用，可执行：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

也可手动安装：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 使用

- 不填密钥：选择离线演示，载入 Python 或 C++ 示例，开始审查。离线模式只运行本地规则。
- 使用模型（目前只尝试deepseek的api）：选择 DeepSeek API，在侧栏输入自己的 Key；也可复制 `.env.example` 为 `.env` 再填写。
- 密钥不会随本包提供。侧栏输入用于浏览器及服务端会话，不自动写入报告。
- 模型模式会将提交的代码及审查上下文发送到配置的 API。不要公开 `.env`。
- 问题与建议合并展示，但各条保留依据状态；模型复核不等于已运行代码或正确性证明。
- 继续追问支持局部修改建议：检查补丁影响的后续引用，并用组合后的代码复核。失败时最多修正一次；展开校验记录可区分历史候选与最后一次失败原因。建议不会自动应用到文件。
- 识别语言取决于文件后缀；支持单文件最多 800 行 / 48 KB。C++ 不需要安装编译器。

## 文件

`app.py` 是网页入口；`review_agent/` 是核心实现；`examples/` 是演示代码；`.streamlit/` 是本机服务配置；[设计说明](docs/DESIGN.md)介绍架构。
`requirements.txt` 是运行依赖，`requirements-dev.txt` 被 setup.ps1 使用并额外安装 pytest 和测试所需 NumPy；`requirements-lock.txt` 保留原开发环境版本供参考。
仓库还包含 `tests/` 自动化测试、`evals/` 合成评估样例和历史实测记录、评估脚本及[验证指南](docs/VALIDATION_GUIDE.md)。不含虚拟环境、密钥、用户审查报告和课程课件；属于源码运行包，并非免安装的 exe。

命令行离线验证：

```powershell
.\.venv\Scripts\python.exe -m review_agent examples/buggy_order.py --demo
.\.venv\Scripts\python.exe -m review_agent examples/buggy_order.cpp --demo
```

## 自动化测试与评估

在本仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app.py evaluate.py evaluate_followup.py score_evaluation.py benchmark_review.py record_demo.py review_agent tests
.\.venv\Scripts\python.exe evaluate.py --demo --output reports/eval-demo.json
```

测试使用本地工具和模拟模型，不需要 API Key，也不会调用真实模型。覆盖 Python/C++ 规则、Agent 工具循环、证据校验、追问、网页、接口错误处理，以及静态发现补回和超过报告容量时的截断提示。通过测试说明这些场景的行为符合断言，不代表通用审查准确率。

真实 API 验证需要在本机 `.env` 中配置**自己的** Key 和可用模型名，运行以下命令会产生 API 用量，仅发送仓库内的合成代码：

```powershell
.\.venv\Scripts\python.exe record_demo.py --output reports/live-demo-current.json
.\.venv\Scripts\python.exe evaluate.py --cases evals/quality.json --strategy full --output reports/quality-current.json
.\.venv\Scripts\python.exe evaluate_followup.py --output reports/followup-current.json
```

`record_demo.py` 只发送内置的 Python/C++ 两份合成代码，记录公开工具调用、工具反馈、模型输出、复核和最终报告；本轮已完成的记录见 [submission-20261002.json](evals/results/submission-20261002.json)。更多评估样例也保留完整报告、耗时和 token；质量结论仍需逐条检查。[评估说明](docs/QUALITY_EVALUATION.md)区分 2026-09-28 历史开发结果和当前版本验证。`reports/` 与 `.env` 已忽略，不会因为运行评估而自动上传。不要把密钥写入源码或报告；也不要把本机 `.env` 加入 Git。
