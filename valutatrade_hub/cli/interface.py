"""
Командный интерфейс приложения (CLI).
"""

import sys
import cmd
import shlex
from typing import Optional
from prettytable import PrettyTable

from ..infra.database import DatabaseManager
from ..infra.settings import SettingsLoader
from ..core.usecases import UserUseCases, PortfolioUseCases
from ..core.exceptions import (
    InsufficientFundsError, CurrencyNotFoundError,
    UserNotFoundError, AuthenticationError, ValidationError
)
from ..parser_service.updater import RatesUpdater
from ..logging_config import setup_logging


class ValutaTradeCLI(cmd.Cmd):
    """Интерактивный CLI для ValutaTrade Hub."""

    intro = """
ValutaTrade Hub - Терминал валют

Доступные команды:
  register <username> <password>    - Регистрация
  login <username> <password>       - Вход в систему
  logout                           - Выход из системы
  
  portfolio [--base CURRENCY]       - Показать портфель
  buy <currency> <amount>          - Купить валюту
  sell <currency> <amount>         - Продать валюту
  
  get_rate <from> <to>             - Получить курс
  update_rates [source]            - Обновить курсы
  show_rates [--top N] [--currency CURRENCY] - Показать курсы
  
  help                             - Показать справку
  exit                             - Выход из программы

Используйте 'help <команда>' для подробной справки.
"""
    prompt = ">>> "

    def __init__(self):
        """Инициализация CLI."""
        super().__init__()

        # Настройка логирования
        settings = SettingsLoader()
        log_file = settings.get("log_file", "logs/actions.log")
        setup_logging(log_file)

        # Инициализация зависимостей
        self.db = DatabaseManager()
        self.user_uc = UserUseCases(self.db)
        self.portfolio_uc = PortfolioUseCases(self.db)
        self.rates_updater = RatesUpdater()

        # Текущий пользователь
        self.current_user: Optional[dict] = None

    def _check_auth(self):
        """Проверяет, авторизован ли пользователь."""
        if not self.current_user:
            raise AuthenticationError("Сначала выполните команду login")

    def do_register(self, arg):
        """
        Регистрация нового пользователя.
        Использование: register <username> <password>
        """
        try:
            args = shlex.split(arg)
            if len(args) != 2:
                print("Использование: register <username> <password>")
                return

            username, password = args

            print(f"Регистрация пользователя '{username}'...")
            user, portfolio = self.user_uc.register_user(username, password)

            print(f"\nПользователь '{username}' успешно зарегистрирован (id={user.user_id})")
            print("Создан начальный портфель с кошельком USD")
            print(f"\nТеперь выполните: login {username} {password}")

        except ValidationError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")

    def do_login(self, arg):
        """
        Вход в систему.
        Использование: login <username> <password>
        """
        try:
            args = shlex.split(arg)
            if len(args) != 2:
                print("Использование: login <username> <password>")
                return

            username, password = args

            print(f"Вход пользователя '{username}'...")
            user = self.user_uc.login_user(username, password)
            self.current_user = {
                'id': user.user_id,
                'username': user.username,
                'registration_date': user.registration_date
            }

            print(f"\nВы вошли как '{username}' (id={user.user_id})")
            print(f"Дата регистрации: {user.registration_date.strftime('%Y-%m-%d %H:%M')}")

            # Обновляем приглашение
            self.prompt = f"{username} >>> "

        except (UserNotFoundError, AuthenticationError) as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")

    def do_logout(self, arg):
        """
        Выход из системы.
        Использование: logout
        """
        if self.current_user:
            print(f"До свидания, {self.current_user['username']}!")
            self.current_user = None
            self.prompt = ">>> "
        else:
            print("Вы не вошли в систему")

    def do_portfolio(self, arg):
        """
        Показать портфель.
        Использование: portfolio [--base CURRENCY]
        Пример: portfolio --base USD
        """
        try:
            self._check_auth()

            # Парсим аргументы
            args = shlex.split(arg)
            base_currency = "USD"

            i = 0
            while i < len(args):
                if args[i] == "--base" and i + 1 < len(args):
                    base_currency = args[i + 1]
                    i += 2
                else:
                    i += 1

            print(f"Загружаю портфель пользователя '{self.current_user['username']}'...")

            portfolio_info = self.portfolio_uc.show_portfolio(
                self.current_user['id'],
                base_currency
            )

            # Создаем таблицу
            table = PrettyTable()
            table.field_names = ["Валюта", "Баланс", f"Стоимость ({base_currency})", "Информация"]
            table.align["Валюта"] = "l"
            table.align["Баланс"] = "r"
            table.align[f"Стоимость ({base_currency})"] = "r"
            table.align["Информация"] = "l"

            total_value = 0

            for wallet in portfolio_info['wallets']:
                table.add_row([
                    wallet['currency_code'],
                    f"{wallet['balance']:,.4f}",
                    f"{wallet['value_in_base']:,.2f}",
                    wallet['currency_info']
                ])
                total_value += wallet['value_in_base']

            print(f"\nПортфель пользователя '{portfolio_info['username']}' (база: {base_currency})")
            print(f"Курсы обновлены: {portfolio_info['rates_updated_at'] or 'Неизвестно'}")
            print(table)

            if total_value > 0:
                print(f"\nИТОГО: {total_value:,.2f} {base_currency}")
            else:
                print("\nПортфель пуст. Используйте команду buy для покупки валюты.")

        except AuthenticationError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")

    def do_buy(self, arg):
        """
        Купить валюту.
        Использование: buy <currency> <amount>
        Пример: buy BTC 0.01
        """
        try:
            self._check_auth()

            args = shlex.split(arg)
            if len(args) != 2:
                print("Использование: buy <currency> <amount>")
                print("Пример: buy BTC 0.01")
                return

            currency = args[0].upper()
            try:
                amount = float(args[1])
            except ValueError:
                print("Ошибка: amount должен быть числом")
                return

            print(f"Покупаю {amount} {currency}...")

            result = self.portfolio_uc.buy_currency(
                self.current_user['id'],
                currency,
                amount
            )

            print(f"\n{result['message']}")
            print("\nИзменения в портфеле:")
            print(f"  - {currency}: было {result['details']['old_balance']:.4f} → стало {result['details']['new_balance']:.4f}")
            print(f"  - USD: остаток {result['details']['usd_balance_after']:.2f}")
            print(f"\nОценочная стоимость покупки: {result['details']['cost_usd']:.2f} USD")

        except (ValidationError, InsufficientFundsError, CurrencyNotFoundError) as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")

    def do_sell(self, arg):
        """
        Продать валюту.
        Использование: sell <currency> <amount>
        Пример: sell BTC 0.005
        """
        try:
            self._check_auth()

            args = shlex.split(arg)
            if len(args) != 2:
                print("Использование: sell <currency> <amount>")
                print("Пример: sell BTC 0.005")
                return

            currency = args[0].upper()
            try:
                amount = float(args[1])
            except ValueError:
                print("Ошибка: amount должен быть числом")
                return

            print(f"Продаю {amount} {currency}...")

            result = self.portfolio_uc.sell_currency(
                self.current_user['id'],
                currency,
                amount
            )

            print(f"\n{result['message']}")
            print("\nИзменения в портфеле:")
            print(f"  - {currency}: было {result['details']['old_balance']:.4f} → стало {result['details']['new_balance']:.4f}")
            print(f"  - USD: было {result['details']['usd_old_balance']:.2f} → стало {result['details']['usd_new_balance']:.2f}")
            print(f"\nОценочная выручка: {result['details']['revenue_usd']:.2f} USD")

        except (ValidationError, InsufficientFundsError, CurrencyNotFoundError) as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")

    def do_get_rate(self, arg):
        """
        Получить курс валюты.
        Использование: get_rate <from> <to>
        Пример: get_rate USD BTC
        """
        try:
            args = shlex.split(arg)
            if len(args) != 2:
                print("Использование: get_rate <from> <to>")
                print("Пример: get_rate USD BTC")
                return

            from_currency = args[0].upper()
            to_currency = args[1].upper()

            print(f"Получаю курс {from_currency} → {to_currency}...")

            rate_info = self.portfolio_uc.get_rate(from_currency, to_currency)

            print(f"\n💱 Курс {rate_info['from_currency']}→{rate_info['to_currency']}: {rate_info['rate']:.6f}")
            print(f"Обновлено: {rate_info['updated_at']}")
            print(f"Источник: {rate_info['source']}")

            # Показываем обратный курс
            if rate_info['is_direct']:
                reverse_rate = 1 / rate_info['rate']
                print(f"Обратный курс {rate_info['to_currency']}→{rate_info['from_currency']}: {reverse_rate:.6f}")

        except (ValidationError, CurrencyNotFoundError) as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")

    def do_update_rates(self, arg):
        """
        Обновить курсы валют.
        Использование: update_rates [source]
        Пример: update_rates (обновить все)
                update_rates coingecko (только крипто)
                update_rates exchangerate (только фиат)
        """
        try:
            args = shlex.split(arg)
            source = args[0] if args else None

            if source and source not in ['coingecko', 'exchangerate']:
                print("Ошибка: источник должен быть 'coingecko' или 'exchangerate'")
                return

            print("Обновляю курсы валют...")

            results = self.rates_updater.run_update(source)

            if results['success']:
                print("\nОбновление успешно завершено!")
                print(f"Источники: {', '.join(results['sources_updated'])}")
                print(f"Получено курсов: {results['rates_count']}")
                print(f"Время обновления: {results['timestamp']}")
            else:
                print("\nОбновление завершено с ошибками")
                print(f"Успешные источники: {', '.join(results['sources_updated'])}")
                print(f"Получено курсов: {results['rates_count']}")
                print("Ошибки:")
                for error in results['errors']:
                    print(f"   - {error['source']}: {error['error']}")

        except Exception as e:
            print(f"Неожиданная ошибка: {e}")

    def do_show_rates(self, arg):
        """
        Показать курсы валют.
        Использование: show_rates [--top N] [--currency CURRENCY]
        Пример: show_rates
                show_rates --top 5
                show_rates --currency BTC
        """
        try:
            args = shlex.split(arg)
            top = None
            currency = None

            i = 0
            while i < len(args):
                if args[i] == "--top" and i + 1 < len(args):
                    try:
                        top = int(args[i + 1])
                    except ValueError:
                        print("Ошибка: --top должен быть числом")
                        return
                    i += 2
                elif args[i] == "--currency" and i + 1 < len(args):
                    currency = args[i + 1].upper()
                    i += 2
                else:
                    i += 1

            print("Загружаю курсы валют...")

            rates_data = self.portfolio_uc.get_exchange_rates()
            pairs = rates_data.get("pairs", {})

            if not pairs:
                print("Локальный кеш курсов пуст. Выполните 'update_rates', чтобы загрузить данные.")
                return

            # Фильтруем курсы если нужно
            filtered_pairs = {}

            if currency:
                # Фильтруем по валюте
                for pair_key, rate_info in pairs.items():
                    if pair_key.startswith(currency + "_") or pair_key.endswith("_" + currency):
                        filtered_pairs[pair_key] = rate_info
            else:
                filtered_pairs = pairs

            if not filtered_pairs:
                print(f"Курс для валюты '{currency}' не найден в кеше.")
                return

            # Сортируем
            sorted_pairs = sorted(
                filtered_pairs.items(),
                key=lambda x: x[1]['rate'],
                reverse=True
            )

            # Применяем ограничение по top если указано
            if top:
                sorted_pairs = sorted_pairs[:top]

            # Создаем таблицу
            table = PrettyTable()
            table.field_names = ["Пара валют", "Курс", "Обновлено", "Источник"]
            table.align["Пара валют"] = "l"
            table.align["Курс"] = "r"
            table.align["Обновлено"] = "l"
            table.align["Источник"] = "l"

            for pair_key, rate_info in sorted_pairs:
                table.add_row([
                    pair_key,
                    f"{rate_info['rate']:.6f}",
                    rate_info['updated_at'],
                    rate_info['source']
                ])

            print(f"\nКурсы валют из кеша (обновлено: {rates_data.get('last_refresh', 'Неизвестно')})")
            print(table)

        except Exception as e:
            print(f"Неожиданная ошибка: {e}")

    def do_exit(self, arg):
        """
        Выход из программы.
        Использование: exit
        """
        print("\nДо свидания! Спасибо за использование ValutaTrade Hub!")
        return True

    def do_EOF(self, arg):
        """Выход по Ctrl+D."""
        print()  # Новая строка для красоты
        return self.do_exit(arg)

    def default(self, line):
        """Обработка неизвестных команд."""
        print(f"Неизвестная команда: {line}")
        print("Введите 'help' для списка команд")


def main():
    """Точка входа в CLI."""
    cli = ValutaTradeCLI()

    if len(sys.argv) > 1:
        cli.onecmd(' '.join(sys.argv[1:]))
    else:
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\n\nПрервано пользователем. До свидания!")
            sys.exit(0)


if __name__ == "__main__":
    main()