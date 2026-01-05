import shlex
from prettytable import PrettyTable

from valutatrade_hub.core import usecases


# =========================
# HELPERS
# =========================

def print_error(err: Exception):
    print(f"Ошибка: {err}")


def print_success(msg: str):
    print(msg)


# =========================
# COMMAND HANDLERS
# =========================

def handle_register(args: list[str]):
    if "--username" not in args or "--password" not in args:
        raise ValueError("Использование: register --username <name> --password <pass>")

    username = args[args.index("--username") + 1]
    password = args[args.index("--password") + 1]

    msg = usecases.register_user(username, password)
    print_success(msg)


def handle_login(args: list[str]):
    if "--username" not in args or "--password" not in args:
        raise ValueError("Использование: login --username <name> --password <pass>")

    username = args[args.index("--username") + 1]
    password = args[args.index("--password") + 1]

    msg = usecases.login_user(username, password)
    print_success(msg)


def handle_logout(_args: list[str]):
    msg = usecases.logout_user()
    print_success(msg)


def handle_show_portfolio(args: list[str]):
    base = "USD"
    if "--base" in args:
        base = args[args.index("--base") + 1]

    result = usecases.show_portfolio(base)

    table = PrettyTable()
    table.field_names = ["Валюта", "Баланс", f"Стоимость ({base})"]

    for w in result["wallets"]:
        table.add_row([w["currency"], w["balance"], w["value"]])

    print(f"\nПортфель пользователя '{result['username']}' (база: {base})")
    if result["wallets"]:
        print(table)
        print("-" * 40)
        print(f"ИТОГО: {result['total']} {base}")
    else:
        print("Портфель пуст")


def handle_buy(args: list[str]):
    if "--currency" not in args or "--amount" not in args:
        raise ValueError("Использование: buy --currency <CODE> --amount <float>")

    currency = args[args.index("--currency") + 1]
    amount = float(args[args.index("--amount") + 1])

    result = usecases.buy_currency(currency, amount)

    print(f"Покупка выполнена: {amount:.4f} {currency}")
    print(f"- Было: {result['before']:.4f}")
    print(f"- Стало: {result['after']:.4f}")

    if result["rate"]:
        print(f"Курс: {result['rate']} USD/{currency}")
        print(f"Оценочная стоимость: {result['cost']} USD")


def handle_sell(args: list[str]):
    if "--currency" not in args or "--amount" not in args:
        raise ValueError("Использование: sell --currency <CODE> --amount <float>")

    currency = args[args.index("--currency") + 1]
    amount = float(args[args.index("--amount") + 1])

    result = usecases.sell_currency(currency, amount)

    print(f"Продажа выполнена: {amount:.4f} {currency}")
    print(f"- Было: {result['before']:.4f}")
    print(f"- Стало: {result['after']:.4f}")

    if result["rate"]:
        print(f"Курс: {result['rate']} USD/{currency}")
        print(f"Выручка: {result['revenue']} USD")


def handle_get_rate(args: list[str]):
    if "--from" not in args or "--to" not in args:
        raise ValueError("Использование: get-rate --from <CUR> --to <CUR>")

    from_cur = args[args.index("--from") + 1]
    to_cur = args[args.index("--to") + 1]

    result = usecases.get_rate(from_cur, to_cur)

    print(f"Курс {from_cur}→{to_cur}: {result['rate']}")
    print(f"Обратный курс {to_cur}→{from_cur}: {result['reverse']}")


# =========================
# COMMAND ROUTER
# =========================

COMMANDS = {
    "register": handle_register,
    "login": handle_login,
    "logout": handle_logout,
    "show-portfolio": handle_show_portfolio,
    "buy": handle_buy,
    "sell": handle_sell,
    "get-rate": handle_get_rate,
}


def run_cli():
    print("ValutaTrade Hub CLI")
    print("Введите команду или 'exit'\n")

    while True:
        try:
            raw = input("> ").strip()
            if not raw:
                continue

            if raw in ("exit", "quit"):
                print("Выход.")
                break

            parts = shlex.split(raw)
            command = parts[0]
            args = parts[1:]

            if command not in COMMANDS:
                print(f"Неизвестная команда '{command}'")
                continue

            COMMANDS[command](args)

        except Exception as e:
            print_error(e)
