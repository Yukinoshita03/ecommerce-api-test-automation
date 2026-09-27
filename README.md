# 电商 API 自动化测试练习

这是我的 Python 测试开发练习仓库。被测系统是开源项目 [ecommerce-api](https://github.com/Franklindot04/ecommerce-api)；服务端代码保留在原仓库，本仓库用于逐步手写自己的接口测试框架和测试用例。

## 当前状态

主回归测试位于 `tests/`，目前可收集 16 个执行用例：商品列表、商品详情、商品不存在、创建商品缺少必填字段、非法价格和库存（2 个参数化用例）、创建商品成功（2 个参数化用例）、HTTP 404 的 `raise_for_status()` 行为、未登录访问受保护接口、登录后访问当前用户接口、购物车添加/查询/删除流程，以及正常下单、空购物车、库存被其他订单耗尽和订单归属检查。各订单场景的前置数据与预期见 [订单用例设计](docs/order-test-cases.md)。库存场景按顺序执行，不是并发压力测试。

`practice/` 保存 pytest 异常处理、环境变量和跳过标记练习，不混入默认 API 回归集。练习可单独运行：

```bash
.venv/bin/python -m pytest practice -q
```

创建商品成功测试、登录流程、购物车流程和订单用例都会写入被测服务数据库，并标记为 `stateful`。被测服务目前没有删除商品、订单或用户的接口；认证、购物车和订单用例使用唯一用户名，订单写入用例还会创建唯一商品。双用户用例使用独立 Session，测试后清理客户端 token 和各自购物车；注册用户、创建的商品和订单会保留在本地测试数据库中，成功下单会扣减本次新商品的库存。因此这些用例应运行在可重置的本地测试服务上。

## 计划使用的技术

- Python、pytest、requests：发送 HTTP 请求并编写断言。
- pytest fixture、参数化：管理测试数据和复用准备步骤。
- YAML、logging、Allure：管理用例数据、记录排查信息、生成报告。
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

当前测试代码由我逐步手写，覆盖范围会随着学习进度继续扩展。
