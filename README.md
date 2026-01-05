# Final Project: Валютный кошелёк и трейдинг

**Автор:** Леонид Найданов  
**Группа:** <твоя группа>  
**Дата:** 2026-01-05

---

## Описание проекта

Проект реализует консольное приложение для работы с виртуальным валютным кошельком, которое позволяет пользователям:

- Регистрироваться и входить в систему.
- Управлять портфелем фиатных и криптовалют.
- Покупать и продавать валюту.
- Получать актуальные курсы валют.
- Отслеживать историю транзакций.

Система построена с использованием объектно-ориентированного программирования, с обработкой исключений, логированием операций и модульной структурой.

---

## Структура проекта

```

finalproject_Naydanov_Leonid/
│
├── data/
│    ├── users.json           # Пользователи
│    ├── portfolios.json      # Портфели пользователей
│    └── rates.json           # Курсы валют
├── valutatrade_hub/
│    ├── **init**.py
│    ├── logging_config.py    # Настройка логов
│    ├── decorators.py        # @log_action
│    ├── core/
│    │    ├── **init**.py
│    │    ├── currencies.py   # Классы валют
│    │    ├── exceptions.py   # Пользовательские ошибки
│    │    ├── models.py       # Пользователи, кошельки, портфели
│    │    ├── usecases.py     # Логика buy/sell/get-rate
│    │    └── utils.py        # Валидация, конвертация
│    ├── infra/
│    │    ├─ **init**.py
│    │    ├── settings.py     # Singleton SettingsLoader
│    │    └── database.py     # Singleton DatabaseManager
│    └── cli/
│         ├─ **init**.py
│         └─ interface.py     # Командный интерфейс
├── main.py
├── Makefile
├── pyproject.toml
├── poetry.lock
├── README.md
└── .gitignore

````

---

## Установка

1. Установите Python 3.12.x (рекомендуется через pyenv или официальные дистрибутивы).
2. Установите [Poetry](https://python-poetry.org/docs/#installation):

```bash
curl -sSL https://install.python-poetry.org | python3 -
````

3. Клонируйте проект:

```bash
git clone <ссылка на репозиторий>
cd finalproject_Naydanov_Leonid
```

4. Установите зависимости через Makefile:

```bash
make install
```

5. Запустите CLI:

```bash
make run
```

---

## Команды CLI

После запуска `make run` вы попадёте в интерактивный CLI. Доступные команды:

| Команда                                         | Описание                                                                   |
| ----------------------------------------------- | -------------------------------------------------------------------------- |
| `register --username <имя> --password <пароль>` | Регистрация нового пользователя                                            |
| `login --username <имя> --password <пароль>`    | Вход в систему                                                             |
| `show-portfolio [--base <валюта>]`              | Показать портфель и итоговую стоимость в базовой валюте (по умолчанию USD) |
| `buy --currency <код> --amount <количество>`    | Купить валюту                                                              |
| `sell --currency <код> --amount <количество>`   | Продать валюту                                                             |
| `get-rate --from <код> --to <код>`              | Получить актуальный курс валюты                                            |
| `help`                                          | Список команд                                                              |
| `exit`                                          | Выйти из CLI                                                               |

---

## Примеры использования

```text
Введите команду (help для списка команд, exit для выхода)
> register --username alice --password 1234
Пользователь 'alice' зарегистрирован (id=1)

> login --username alice --password 1234
Вы вошли как 'alice'

> show-portfolio
Портфель пользователя 'alice':
- USD: 0.00 → 0.00 USD
- BTC: 0.00 → 0.00 USD
ИТОГО: 0.00 USD

> buy --currency USD --amount 1000
Покупка выполнена: 1000 USD

> buy --currency BTC --amount 0.05
Покупка выполнена: 0.0500 BTC по курсу 59337.21 USD/BTC

> show-portfolio
Портфель пользователя 'alice':
- USD: 1000.00 → 1000.00 USD
- BTC: 0.0500 → 2965.00 USD
ИТОГО: 3,965.00 USD

> sell --currency BTC --amount 0.02
Продажа выполнена: 0.0200 BTC
Оценочная выручка: 1,186.74 USD

> get-rate --from USD --to BTC
Курс USD→BTC: 0.00001685 (обновлено: 2025-10-09 10:30:00)
Обратный курс BTC→USD: 59337.21
```

---

## Настройка

* Путь к данным и настройкам хранится в `infra/settings.py`.
* Логи операций пишутся в `logs/actions.log` (с ротацией и уровнем INFO).
* Обновление курсов можно настроить через `rates.json` или подключить Parser Service (для реального API).

---

## Зависимости

* Python 3.12.x
* Poetry
* `prettytable` — для красивого отображения таблиц
* `ruff` — для статического анализа кода

---

## Автор

Leonid Naydanov