#!/usr/bin/env python3
"""
Главный модуль приложения валютного кошелька.
"""

import sys
from valutatrade_hub.cli.interface import main

if __name__ == "__main__":
    sys.exit(main() or 0)