# 电商 API 自动化测试练习

这是我的 Python 测试开发练习仓库。被测系统是开源项目 [ecommerce-api](https://github.com/Franklindot04/ecommerce-api)；服务端代码保留在原仓库，本仓库用于逐步手写自己的接口测试框架和测试用例。

## 当前状态

主回归测试位于 `tests/`，目前可收集 57 个正常执行用例，另有 1 个默认跳过的 Hook 失败演示：17 个接口用例覆盖商品、HTTP 错误、认证、购物车及订单；40 个本地用例检查地址配置、YAML 数据格式、请求超时、报告脱敏及 JSONPath 提取。商品非法值用例先校验 YAML 结构，再生成参数化测试；新增同类输入只需向 YAML 添加数据行。各订单场景的前置数据与预期见 [订单用例设计](docs/order-test-cases.md)。库存场景按顺序执行，不是并发压力测试。

`practice/` 保存 pytest 异常处理、环境变量和跳过标记练习，不混入默认 API 回归集。练习可单独运行：

```bash
.venv/bin/python -m pytest practice -q
```

创建商品成功测试、登录流程、购物车流程和订单用例都会写入被测服务数据库，并标记为 `stateful`。认证、购物车和订单用例使用唯一用户名；购物车与订单用例新建唯一商品，创建商品成功用例也使用唯一名称。双用户用例使用独立 Session。测试结束时关闭客户端、移除 token，并只清理本次账号的购物车；若服务不可用，购物车清理可能失败。被测服务没有删除用户、商品或订单的接口，所以这些记录会保留在本地测试数据库中，成功下单还会扣减本次新商品的库存。写入用例应运行在可重置的本地测试服务上。

## 当前技术与后续方向

- Python、pytest、requests：发送 HTTP 请求并编写断言。
- pytest fixture、参数化：管理测试数据和复用准备步骤。
- YAML：已用于商品非法值参数化，并在加载时校验用例结构。
- Allure：已添加用例分组、中文标题、场景步骤和接口请求/响应附件。
- logging：已记录请求方法、路径、状态码、耗时和异常类型。
- CI：自动运行回归测试。

以上按条目区分当前能力与后续目标；AI 和 CI 状态见各节说明。

## 启动被测服务

在另一个目录克隆并启动原项目：

```bash
git clone https://github.com/Franklindot04/ecommerce-api.git
cd ecommerce-api
cp .env.example .env
docker compose build api
docker compose run --rm --no-deps api alembic upgrade head
docker compose up -d
curl http://localhost:8000/health
```

接口文档：<http://localhost:8000/docs>。结束练习后，在被测服务目录运行 `docker compose down`。

## 运行测试

启动被测服务后，在仓库根目录安装依赖并运行主回归测试：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests -q
```

测试地址依次取 `--base-url` 命令行参数、`TEST_BASE_URL` 环境变量、默认值 `http://localhost:8000`。地址不能为空，且必须是带主机名的 HTTP(S) URL；用例始终通过 `ApiClient` 拼接接口路径。下面三种方式可选择同一套测试：

```bash
.venv/bin/python -m pytest tests/test_products.py::test_product_list -q
TEST_BASE_URL=http://localhost:8000 .venv/bin/python -m pytest tests/test_products.py::test_product_list -q
.venv/bin/python -m pytest tests/test_products.py::test_product_list --base-url=http://localhost:8000 -q
```

需要验证优先级时，可把环境变量设为无效端口，同时用 `--base-url` 指向本地测试服务。账号、商品和订单 ID 在运行时生成或从本次响应获取，不保存在 YAML 中。

当前测试代码由我逐步手写，覆盖范围会随着学习进度继续扩展。

## Allure 报告

在仓库根目录执行（每次运行使用新的结果目录，避免混入旧结果）：

```bash
.venv/bin/python -m pytest tests --alluredir=/tmp/ecommerce-allure-run1
allure generate /tmp/ecommerce-allure-run1 -o /tmp/ecommerce-report-run1
allure open /tmp/ecommerce-report-run1
```

Python 插件随 requirements.txt 安装；生成网页还需要单独安装 Allure CLI。若终端找不到 `allure`，本机可使用 `/Users/tankaiwen/.npm-global/bin/allure`。`/tmp` 目录是临时存储，需长期留存时选择自己可写的目录。

报告中 feature 对应用例分组，title 对应中文名称，step 展示执行过程。ApiClient 为每次请求自动记录步骤、结构化输入、响应状态码与 JSON 正文；异常记录类型并继续向外抛出。密码、token 等凭据字段递归脱敏，不记录原始请求头、非结构化请求正文及非 JSON 响应正文。附件在成功和失败时都会记录；pytest 的失败断言由插件自动收集。练习目录也添加了 Allure 展示，可用同样参数单独运行。

## JSONPath 接口关联

`common/jsonpath_utils.py` 的 `extract_one(body, expression)` 要求路径恰好匹配一个值；字段缺失或匹配多个值时给出明确的断言信息。认证、购物车和订单测试使用它提取本次响应的 token、商品 ID、购物车条目 ID 和订单 ID，再传给后续请求。原有状态码及业务断言保持不变。Allure 只记录提取表达式，不附加提取值，避免将 token 写入步骤附件。

```python
order_id = extract_one(created_order, "$.id")
response = client.request("GET", f"/orders/{order_id}")
```

## 失败上下文

`tests/conftest.py` 在每条测试的生命周期内收集接口附件，并在 setup、call 或 teardown 失败时保存结构化 JSON，同时附到 Allure。包含用例标识、阶段、耗时、异常类型、异常信息、截至失败时的请求响应证据和本阶段捕获日志。每次运行使用独立子目录，每个失败阶段生成一个文件；通过及跳过的阶段不生成失败 JSON。

```bash
RUN_HOOK_DEMO=1 .venv/bin/python -m pytest tests/test_hook_demo.py -v -s --failure-dir=/tmp/ecommerce-failures --alluredir=/tmp/ecommerce-hook-results
```

这条演示故意断言失败，预期为 1 failed；终端打印 JSON 的绝对路径。不启用时默认跳过，不访问真实接口或修改数据库。

默认输出为 `reports/failures/<运行编号>/`，目录已被 Git 忽略。字段凭据递归脱敏，收集中识别出的凭据也从异常和日志文本中隐藏；不复制 traceback 源码或局部变量。原始 pytest/Allure 自带的 traceback 并不由此收集器重新脱敏，因此不要在断言消息或源码里写真实凭据。仅在本次 pytest 测试线程里通过公共附件入口记录的证据会被关联；后台线程的请求需要后续显式传播上下文。是否调用模型由 AI_ANALYSIS_MODE 决定，详见下节。

## AI 失败分析

AI 由 `tests/conftest.py` 的失败报告 Hook 触发，只有 `report.failed` 时分析。ApiClient 仅记录请求、响应和异常证据。预期的 404、422 和 `pytest.raises(Timeout)` 用例通过时不调用模型；HTTP 200 后断言失败，以及 setup / teardown 失败也能分析。

`AI_ANALYSIS_MODE` 默认为 `off`：

- `off`：只保存原始失败上下文。
- `fake`：固定模拟结果，用于验证流程，不消费模型额度。
- `real`：通过 `AI_ENDPOINT`（完整 chat/completions 地址）、`AI_MODEL`、`AI_API_KEY` 调用兼容服务。

```bash
RUN_HOOK_DEMO=1 AI_ANALYSIS_MODE=fake .venv/bin/python -m pytest tests/test_hook_demo.py -v -s --failure-dir=/tmp/ecommerce-ai-failures --alluredir=/tmp/ecommerce-ai-hook-results
allure generate /tmp/ecommerce-ai-hook-results -o /tmp/ecommerce-ai-hook-report
allure open /tmp/ecommerce-ai-hook-report
```

演示预期为 `1 failed`，包含“失败上下文 (call)”和“AI 分析结果 (call)”附件。默认跳过，不访问真实业务服务。运行中产生的上下文 JSON 和 `*-ai.json` 分析文件放在同一个独立运行目录。

真实模式的配置（Key 由本地环境安全提供，不写入代码、命令示例或 Git）：

```bash
export AI_ENDPOINT=https://api.deepseek.com/chat/completions
export AI_MODEL=deepseek-flash
# 先在本地配置 AI_API_KEY，再显式运行：
RUN_HOOK_DEMO=1 AI_ANALYSIS_MODE=real .venv/bin/python -m pytest tests/test_hook_demo.py --alluredir=/tmp/ecommerce-ai-real-results
```

提示词位于 `common/ai/prompts/failure_analysis.txt`，要求区分阶段、事实和假设，并说明证据不足之处。模拟用例通过以下 marker 显式提供背景，不依赖自动猜测：

```python
@pytest.mark.analysis_context(
    request_execution="mocked",
    purpose="验证商品名称断言",
    expected_behavior="名称应为 Keyboard",
)
```

模型客户端默认请求超时为 30 秒（Requests 的网络超时，不是严格的总运行期限），不自动重试。模型异常、配置缺失或字段校验失败时生成“AI 分析不可用”附件，保留原测试报告、失败上下文及 fixture 收尾。AI 输出供人工复核，不自动修改测试结果或代码。多个阶段失败时分别分析；启用真实模式会产生相应调用费用。当前整合流程使用模拟模型验证，之前的真实模型联调证明客户端可用，不等于所有失败原因都能准确识别。
