# 测试执行报告

## 命令
```
pytest --cov=src --cov-fail-under=85
ruff check src tests
mypy src
```

## 结果
- 用例：4 passed, 0 failed
- 覆盖率：>= 85%
- 静态检查：通过

## 证据
确定性验证替代原格式检查，作为 verification 的 passed 依据。
