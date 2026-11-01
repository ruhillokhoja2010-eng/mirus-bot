# mathx.py
import ast, math
from aiogram import Router, F, types
from aiogram.filters import Command

router = Router()

ALLOWED = {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd}
FUNCS = {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
         "log": math.log, "abs": abs, "round": round, "min": min, "max": max}
NAMES = {"pi": math.pi, "e": math.e}

def safe_eval(expr: str) -> float:
    if len(expr) > 200:
        raise ValueError("слишком длинный пример")
    tree = ast.parse(expr.replace("^", "**"), mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError("только числа")
        if isinstance(node, (ast.BinOp, ast.UnaryOp)) and type(node.op) not in ALLOWED:
            raise ValueError("такая операция не разрешена")
        if isinstance(node, ast.Name) and node.id not in FUNCS and node.id not in NAMES:
            raise ValueError("неизвестное слово")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            if isinstance(node.right, ast.Constant) and abs(node.right.value) > 1000:
                raise ValueError("слишком большая степень")
    return eval(compile(tree, "<math>", "eval"), {"__builtins__": {}}, {**FUNCS, **NAMES})

@router.message(Command("math"))
async def cmd_math(message: types.Message):
    expr = (message.text or "").replace("/math", "", 1).strip()
    if not expr:
        await message.answer("Пример: /math sqrt(144) + 2^10")
        return
    try:
        res = safe_eval(expr)
        res = round(res, 6) if isinstance(res, float) else res
        await message.answer(f"`{expr} = {res}`", parse_mode="Markdown")
    except ZeroDivisionError:
        await message.answer("Деление на ноль.")
    except Exception:
        await message.answer("Не понял пример. Только числа, + - * / ^ ( ) и sqrt, sin, cos, log.")
