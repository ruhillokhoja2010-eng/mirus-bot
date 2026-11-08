# -*- coding: utf-8 -*-
"""Калькулятор Mirus AI: безопасный разбор выражений и логика кнопочного калькулятора."""
import ast
import math
import operator
import re

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_UN = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {"sqrt": math.sqrt}
_CONSTS = {"pi": math.pi}
MAX_POW = 50

def normalize(expr: str) -> str:
    s = expr.strip().replace(",", ".").replace("×", "*").replace("÷", "/").replace("−", "-").replace("•", "*")
    s = s.replace("^", "**")
    # 50% -> (50/100); работает и для 200*10% -> 200*(10/100)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", s)
    return s

def _ev(node):
    if isinstance(node, ast.Expression):
        return _ev(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Pow):
            base, exp = _ev(node.left), _ev(node.right)
            if abs(exp) > MAX_POW:
                raise ValueError("power too big")
            return base ** exp
        if type(node.op) in _BIN:
            return _BIN[type(node.op)](_ev(node.left), _ev(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
        return _UN[type(node.op)](_ev(node.operand))
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS and len(node.args) == 1:
        return _FUNCS[node.func.id](_ev(node.args[0]))
    raise ValueError("unsupported")

def evaluate(expr: str):
    """Считает выражение. Бросает ValueError, если выражение некорректно."""
    src = normalize(expr)
    if not src:
        raise ValueError("empty")
    try:
        tree = ast.parse(src, mode="eval")
        value = _ev(tree)
    except (SyntaxError, ZeroDivisionError, OverflowError, TypeError) as e:
        raise ValueError(str(e))
    if isinstance(value, complex) or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        raise ValueError("bad result")
    return value

def fmt(value) -> str:
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return f"{value:.10g}"
    return str(value)

def pretty(expr: str) -> str:
    return expr.replace("**", "^").replace("*", "×").replace("/", "÷").replace("-", "−")

# ---------- кнопочный калькулятор ----------
KEYPAD_ROWS = [
    ["C", "⌫", "%", "÷"],
    ["7", "8", "9", "×"],
    ["4", "5", "6", "−"],
    ["1", "2", "3", "+"],
    ["0", ".", "="],
]
_BTN_TO_INNER = {"÷": "/", "×": "*", "−": "-"}
_OPS = "+-*/"

def press(expr: str, key: str):
    """Нажатие кнопки. Возвращает (новое_выражение, ошибка_bool)."""
    key = _BTN_TO_INNER.get(key, key)
    if key == "C":
        return "", False
    if key == "⌫":
        return expr[:-1], False
    if key == "=":
        if not expr:
            return "", False
        try:
            return fmt(evaluate(expr)), False
        except ValueError:
            return expr, True
    if key == "%":
        if expr and (expr[-1].isdigit() or expr[-1] == "."):
            return expr + "%", False
        return expr, False
    if key == ".":
        last = re.split(r"[+\-*/]", expr)[-1]
        if "." in last:
            return expr, False
        if last == "":
            return expr + "0.", False
        return expr + ".", False
    if key in _OPS:
        if not expr:
            return ("-" if key == "-" else ""), False
        if expr[-1] in _OPS:
            return expr[:-1] + key, False
        return expr + key, False
    if key.isdigit():
        return expr + key, False
    return expr, False

def preview(expr: str):
    """Текущий результат для показа под выражением, если он считается."""
    if not expr or expr[-1] in _OPS or expr[-1] == ".":
        return None
    try:
        return fmt(evaluate(expr))
    except ValueError:
        return None

def display(expr: str) -> str:
    if not expr:
        return "0"
    return pretty(expr)

INNER_TO_BTN = {"/": "÷", "*": "×", "-": "−"}

def keypad_labels():
    return KEYPAD_ROWS

def is_arithmetic(text: str) -> bool:
    """Похоже ли сообщение на пример без слов: 2+2, 50*2, 10%, (3+4)*2 и т.п."""
    t = text.strip()
    if not t or len(t) > 80:
        return False
    if not re.fullmatch(r"[\d\s\.\,\+\-\*/×÷−\^%\(\)]+", t):
        return False
    return bool(re.search(r"\d", t)) and bool(re.search(r"[\+\-\*/×÷−\^%]", t))