# 可复现验证指南

本指南随 2026-10-02 的仓库补齐工作加入。验证命令均从 CodeLens 仓库根目录运行；输出到被 Git 忽略的 `reports/`，不覆盖已交付的历史记录。

2026-10-02 追问修正后的完整回归：**245 项通过**，Ruff 检查通过。两轮合成追问实测、此前主审工具循环演示及其版本范围见 [QUALITY_EVALUATION.md](QUALITY_EVALUATION.md)。重新运行时应以本机输出为准。

## 安装与离线回归

建议使用 Python 3.11 或 3.12。第一次先运行 `setup.ps1`，或手动安装：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest --collect-only -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app.py evaluate.py evaluate_followup.py score_evaluation.py benchmark_review.py record_demo.py review_agent tests
```

`pyproject.toml` 将测试目录设为 `tests/`，将仓库根加入导入路径。`requirements-dev.txt` 包括运行依赖、pytest 和测试数值计算所需的 NumPy。测试不要求摄像头、TensorFlow、OpenCV、C++ 编译器或真实 API Key；涉及这些库的源码样例只作为文本分析。C++ 静态解析依赖 Tree-sitter，在运行依赖中安装。

| 测试文件 | 核心检查 |
|---|---|
| `tests/test_agent.py` | 工具结果反馈、结构化输出、复核失败、调用预算和会话上下文 |
| `tests/test_tools.py`、`tests/test_cpp.py` | Python/C++ 静态规则、解析失败、边界及注释/字符串误报 |
| `tests/test_verification.py`、`tests/test_claim_checks.py` | 引用定位、规则归属、双端证据、触发条件和保守分流 |
| `tests/test_semantics.py` | 受限计算、切片/广播结果、源码事实和用量计数 |
| `tests/test_followup.py`、`tests/test_app.py` | 补丁定位、方案校验、追问记忆、网页及导出展示 |
| `tests/test_llm.py` | 模拟 HTTP 错误、重试、鉴权失败与响应解析 |
| `tests/test_evaluation.py` | 评分分母、漏检、未完成样例与逐条标注要求 |
| `tests/test_tool_reconciliation.py` | 模型漏写已执行静态检查的发现时，仍保留工具证据与问题 |
| `tests/test_truncation.py` | 候选超量时优先保留高优先级，并明确报告截断 |
| `tests/test_record_demo.py` | 演示记录只保存公开协议字段，写出时过滤已配置密钥 |

工具发现补回、截断和演示记录测试对应本轮提交反馈。模拟模型可稳定重放“模型漏写工具发现”的情况，但不说明真实模型每次都会漏写，也不测量真实服务的检出率。历史 v5 曾记录 203 项通过；本轮增加测试后的数量以当前 `pytest` 输出和本轮验证记录为准，不能沿用旧数量声称完成当前回归。

## 离线评估

```powershell
.\.venv\Scripts\python.exe -m review_agent examples/buggy_order.py --demo
.\.venv\Scripts\python.exe -m review_agent examples/buggy_order.cpp --demo
.\.venv\Scripts\python.exe -m review_agent examples/clean_order.py --demo
.\.venv\Scripts\python.exe -m review_agent examples/clean_order.cpp --demo
.\.venv\Scripts\python.exe evaluate.py --demo --output reports/eval-demo.json
```

默认评估集 `evals/cases.json` 包含 18 个合成输入（12 个 Python、6 个 C++）。离线模式检查本地规则与报告流程，不代表模型能力；它不会发现所有语义缺陷。每个输出样例保留原始输入、预期问题和报告；报告包含逐阶段耗时、工具事件及用量。

## 真实模型演示

先将 `.env.example` 复制为本机 `.env`，填写自己的 `DEEPSEEK_API_KEY` 和当前账户可用的 `DEEPSEEK_MODEL`。网页侧栏输入的 Key 不会自动供命令行评估使用。以下命令需要网络、会消耗 API 额度，仅发送脚本内置或所选 `evals/*.json` 中的合成代码；不会执行这些被审查代码。

```powershell
.\.venv\Scripts\python.exe record_demo.py --output reports/live-demo-current.json
.\.venv\Scripts\python.exe evaluate.py --cases evals/quality.json --strategy full --output reports/quality-current.json
.\.venv\Scripts\python.exe evaluate_followup.py --cases evals/followup.json --output reports/followup-current.json
```

`record_demo.py` 固定使用脚本内两份合成输入，不接受任意源码文件参数。输出包含运行时源码摘要、Python/模型版本、工具调用请求、真实工具反馈、模型 JSON 响应、最终报告及 Markdown。它不记录 API 认证头，也不记录服务端隐藏推理；“完整演示”指可核查的公开工作流，不是模型内部思维。2026-10-02 已完成的记录见 [submission-20261002.json](../evals/results/submission-20261002.json)。

主审评估逐例保存，单例 API 失败被记入结果，最后返回非零退出码。追问评估先用离线报告建立固定上下文，再执行五个合成场景的六轮追问，避免把主审随机性混入追问评价。查看 `raw_candidates` 可以核对修正过程，不能只看最后显示的答案。

如需演示完整用户流程，可在 Web 页面载入仓库合成示例，完成 API 审查，展开“执行记录”、问题证据和限制，然后提问并导出报告。视频可选；导出的 JSON/Markdown 能保留调用与结论，录屏本身不能证明结论正确。

提交新实测记录前，人工确认文件中只含合成源码、非敏感模型输出及运行元数据，并在说明中写明日期、输入集、模型、策略、失败和局限。不要提交 `.env` 或用户业务代码，不能用历史结果冒充本轮运行。

## 质量与速度的复算

历史三策略结果已逐条开发标注，可在不调用模型的情况下复算：

```powershell
.\.venv\Scripts\python.exe score_evaluation.py --output reports/quality-summary-recomputed.json
```

该命令验证原始结果 SHA-256 与标注一一对应。分类包括已命中、错误、缺少上下文、可选建议及重复；会统计待确认噪声和未完成样例，避免只看正式问题造成分数虚高。它复算的是历史结果，并未重新测试当前实现。要评价当前版本，须先重新生成输出，再做相同标准的逐条标注；不能复用旧结果的编号或哈希。

`benchmark_review.py` 用同一份源码在两个独立进程中对比实现。需要另行提供含 `review_agent/` 的历史基线目录；本仓库没有打包历史引擎，不存在默认即可重跑的基线。只使用合成样例时可运行：

```powershell
.\.venv\Scripts\python.exe benchmark_review.py --file evals/performance_fixture.py --baseline-root D:/path/to/baseline --repeats 2 --output reports/performance-current
```

主审三策略、追问和速度对比的测量目标不同。小样本开发回归不代表通用准确率，也不能将不同代码或不同版本的单次耗时当作公平对照。

## 追问修正的定向复跑

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_followup_repair.py tests/test_app.py
.\.venv\Scripts\python.exe evaluate_followup.py --cases evals/followup-repair.json --output reports/followup-repair-current.json
```

第二条命令调用真实 API。检查 `attempts` 的各轮本地/模型校验状态及最终 `answer`，不要把历史候选失败当成当前失败；成功案例还需核对完整使用链与“原代码/未应用建议”的区别。测试修正路径无需 API。
