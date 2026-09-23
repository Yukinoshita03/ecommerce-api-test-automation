# 电商 API 自动化测试练习

这是我的 Python 测试开发练习仓库。被测系统是开源项目 [ecommerce-api](https://github.com/Franklindot04/ecommerce-api)；服务端代码保留在原仓库，本仓库用于逐步手写自己的接口测试框架和测试用例。

## 当前状态

仓库已建立，尚未添加测试代码。后续从商品查询接口开始，逐步覆盖注册登录、购物车、下单、订单状态与模拟支付。

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

## 第一个练习

手写 `GET /products` 的测试：检查 HTTP 状态码为 `200`，响应是列表，并且至少包含一个商品。测试代码会在后续学习时由我自己提交。
