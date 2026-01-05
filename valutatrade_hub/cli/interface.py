from ..core.usecases import register, login, show_portfolio, buy, sell, get_rate

_current_user = None

def run_cli():
    global _current_user
    print("Введите команду (help для списка команд, exit для выхода)")
    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd == "exit":
                break
            if cmd == "help":
                print("Команды: register, login, show-portfolio, buy, sell, get-rate, exit")
                continue

            parts = cmd.split()
            command, args = parts[0], parts[1:]

            if command == "register":
                username = args[args.index("--username")+1]
                password = args[args.index("--password")+1]
                _current_user = register(username, password)
                print(f"Пользователь '{username}' зарегистрирован")
            elif command == "login":
                username = args[args.index("--username")+1]
                password = args[args.index("--password")+1]
                _current_user = login(username, password)
                print(f"Вы вошли как '{username}'")
            elif command == "show-portfolio":
                if not _current_user:
                    print("Сначала выполните login")
                    continue
                wallets = show_portfolio(_current_user.user_id)
                if not wallets:
                    print("Портфель пуст")
                for code, w in wallets.items():
                    print(f"{code}: {w['balance']}")
            elif command == "buy":
                if not _current_user:
                    print("Сначала выполните login")
                    continue
                currency = args[args.index("--currency")+1]
                amount = float(args[args.index("--amount")+1])
                buy(_current_user.user_id, currency, amount)
                print(f"Куплено {amount} {currency}")
            elif command == "sell":
                if not _current_user:
                    print("Сначала выполните login")
                    continue
                currency = args[args.index("--currency")+1]
                amount = float(args[args.index("--amount")+1])
                sell(_current_user.user_id, currency, amount)
                print(f"Продано {amount} {currency}")
            elif command == "get-rate":
                from_code = args[args.index("--from")+1]
                to_code = args[args.index("--to")+1]
                rate, updated_at = get_rate(from_code, to_code)
                print(f"Курс {from_code}->{to_code}: {rate} (обновлено: {updated_at})")
            else:
                print("Неизвестная команда")
        except Exception as e:
            print(f"Ошибка: {e}")
