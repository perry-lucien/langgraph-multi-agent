# QA 沙盒 Docker 镜像
# 预装了常见的 Python Web 开发依赖，供 QA 子代理在容器中测试代码
FROM python:3.11-slim

WORKDIR /code

# 预装常用依赖（覆盖大部分后端测试场景）
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    flask \
    requests \
    pydantic \
    sqlalchemy

COPY . .

CMD ["python", "main.py"]
