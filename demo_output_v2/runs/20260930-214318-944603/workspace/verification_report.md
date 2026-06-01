# 验证报告

## 概述
温度转换 CLI 重构完成，转换逻辑与 CLI 解析分离，输入校验集中处理，
错误统一输出并以非零状态码退出。

## 功能需求覆盖
- FR-1：CLI 接受 value、from_unit、to_unit 三个参数，支持 C/F/K。
- FR-2：convert() 纯函数执行正确转换。
- FR-3：validate_input() 校验数字、单位与绝对零度下限。
- FR-4：校验失败输出错误信息并返回状态码 1。
- FR-5：成功时输出数值与单位。
- FR-6：test_temp_converter.py 覆盖正常、边界与非法输入。

## 质量需求覆盖
- QR-1：转换逻辑（convert）与 CLI（main）分离。
- QR-2：`python -m unittest` 可运行且全部通过。
- QR-3：错误信息清晰可读。
- QR-4：argparse 提供 --help 与示例。

## 验收标准
- AC-1：`python temp_converter.py 100 C F` -> `212 F`
- AC-2：`python temp_converter.py 32 F C` -> `0 C`
- AC-3：`python temp_converter.py 0 C K` -> `273.15 K`
- AC-4：`python temp_converter.py -300 C F` -> 错误，非零退出
- AC-5：`python temp_converter.py abc C F` -> 错误，非零退出
- AC-6：`python temp_converter.py 100 X F` -> 错误，非零退出
- AC-7：`python -m unittest` 全部通过

## 运行方式
```
python -m unittest -v
python verify_acceptance.py
```
