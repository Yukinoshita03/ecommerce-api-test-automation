# 电商 API 自动化测试练习

这是我的 Python 测试开发练习仓库。被测系统是开源项目 [ecommerce-api](https://github.com/Franklindot04/ecommerce-api)；服务端代码保留在原仓库，本仓库用于逐步手写自己的接口测试框架和测试用例。

## 当前状态

已开始手写电商 API 自动化测试，目前覆盖商品列表、商品详情、商品不存在、创建商品缺少必填字段，以及非法价格和库存边界。参数化用例会分别验证价格和库存，因此 pytest 当前执行 6 个测试用例。

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

启动被测服务后，在仓库根目录安装依赖并运行商品接口测试：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests/test_products.py -v
```

当前测试代码由我逐步手写，覆盖范围会随着学习进度继续扩展。
