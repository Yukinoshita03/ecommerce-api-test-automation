# 电商 API 自动化测试练习

这是我的 Python 测试开发练习仓库。被测系统是开源项目 [ecommerce-api](https://github.com/Franklindot04/ecommerce-api)；服务端代码保留在原仓库，本仓库用于逐步手写自己的接口测试框架和测试用例。

## 当前状态

主回归测试位于 `tests/`，目前可收集 35 个执行用例：17 个接口用例覆盖商品、HTTP 错误、认证、购物车及订单；18 个本地用例检查地址配置、YAML 数据格式、请求超时及报告脱敏。商品非法值用例先校验 YAML 结构，再生成参数化测试；新增同类输入只需向 YAML 添加数据行。各订单场景的前置数据与预期见 [订单用例设计](docs/order-test-cases.md)。库存场景按顺序执行，不是并发压力测试。

`practice/` 保存 pytest 异常处理、环境变量和跳过标记练习，不混入默认 API 回归集。练习可单独运行：

```bash
.venv/bin/python -m pytest practice -q
```

创建商品成功测试、登录流程、购物车流程和订单用例都会写入被测服务数据库，并标记为 `stateful`。认证、购物车和订单用例使用唯一用户名；购物车与订单用例新建唯一商品，创建商品成功用例也使用唯一名称。双用户用例使用独立 Session。测试结束时关闭客户端、移除 token，并只清理本次账号的购物车；若服务不可用，购物车清理可能失败。被测服务没有删除用户、商品或订单的接口，所以这些记录会保留在本地测试数据库中，成功下单还会扣减本次新商品的库存。写入用例应运行在可重置的本地测试服务上。

## 计划使用的技术

- Python、pytest、requests：发送 HTTP 请求并编写断言。
- pytest fixture、参数化：管理测试数据和复用准备步骤。
- YAML：已用于商品非法值参数化，并在加载时校验用例结构。
- Allure：已添加用例分组、中文标题、场景步骤和接口请求/响应附件。
- logging：后续用于记录排查信息。
- CI：自动运行回归测试。

这些是学习目标，不代表已经实现。

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
