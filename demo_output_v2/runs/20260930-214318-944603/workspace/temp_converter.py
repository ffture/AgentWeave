"""温度转换 CLI。

模块化设计：
- 纯转换逻辑 convert(value, from_unit, to_unit)
- 输入校验 validate_input(value, from_unit, to_unit)
- CLI 层仅负责解析参数、调用逻辑、统一错误输出
"""

import argparse
import sys

# 单位常量
CELSIUS = "C"
FAHRENHEIT = "F"
KELVIN = "K"
VALID_UNITS = (CELSIUS, FAHRENHEIT, KELVIN)

# 绝对零度（以各单位的数值表示）
ABSOLUTE_ZERO = {
    CELSIUS: -273.15,
    FAHRENHEIT: -459.67,
    KELVIN: 0.0,
}


class TemperatureError(ValueError):
    """温度转换相关的输入错误。"""


# 各源单位到摄氏度的转换函数
_TO_CELSIUS = {
    CELSIUS: lambda v: v,
    FAHRENHEIT: lambda v: (v - 32.0) * 5.0 / 9.0,
    KELVIN: lambda v: v - 273.15,
}

# 摄氏度到各目标单位的转换函数
_FROM_CELSIUS = {
    CELSIUS: lambda c: c,
    FAHRENHEIT: lambda c: c * 9.0 / 5.0 + 32.0,
    KELVIN: lambda c: c + 273.15,
}


def normalize_unit(unit):
    """将单位字符串规范化为大写并校验合法性。"""
    if not isinstance(unit, str):
        raise TemperatureError("单位必须是字符串，且为 C、F 或 K 之一。")
    normalized = unit.strip().upper()
    if normalized not in VALID_UNITS:
        raise TemperatureError(
            "无效的单位 '%s'，仅支持 C（摄氏度）、F（华氏度）、K（开尔文）。" % unit
        )
    return normalized


def validate_input(value, from_unit, to_unit):
    """校验温度值与单位，返回规范化后的 (float_value, from_unit, to_unit)。

    校验失败时抛出 TemperatureError。
    """
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        raise TemperatureError("温度值 '%s' 不是有效数字。" % (value,))

    from_unit = normalize_unit(from_unit)
    to_unit = normalize_unit(to_unit)

    if numeric < ABSOLUTE_ZERO[from_unit]:
        raise TemperatureError(
            "温度值 %s %s 低于绝对零度（%s %s）。"
            % (numeric, from_unit, ABSOLUTE_ZERO[from_unit], from_unit)
        )

    return numeric, from_unit, to_unit


def convert(value, from_unit, to_unit):
    """纯转换函数：将 value 从 from_unit 转换到 to_unit。

    输入会被校验；返回转换后的浮点数值。
    """
    numeric, from_unit, to_unit = validate_input(value, from_unit, to_unit)
    celsius = _TO_CELSIUS[from_unit](numeric)
    return _FROM_CELSIUS[to_unit](celsius)


def format_result(value, unit):
    """统一输出格式：保留必要小数位，去除多余尾零。"""
    text = "%.2f" % value
    text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        text = "0"
    return "%s %s" % (text, unit)


def build_parser():
    """构建 argparse 解析器，提供清晰的帮助信息。"""
    parser = argparse.ArgumentParser(
        prog="temp_converter.py",
        description="温度转换工具，支持摄氏度(C)、华氏度(F)、开尔文(K)。",
        epilog=(
            "示例：\n"
            "  python temp_converter.py 100 C F   # 输出 212 F\n"
            "  python temp_converter.py 32 F C    # 输出 0 C\n"
            "  python temp_converter.py 0 C K     # 输出 273.15 K"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("value", help="温度数值，例如 100 或 -40.5")
    parser.add_argument("from_unit", help="源单位：C、F 或 K")
    parser.add_argument("to_unit", help="目标单位：C、F 或 K")
    return parser


def main(argv=None):
    """CLI 入口：解析参数、调用转换、统一错误输出。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = convert(args.value, args.from_unit, args.to_unit)
    except TemperatureError as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 1
    print(format_result(result, normalize_unit(args.to_unit)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
