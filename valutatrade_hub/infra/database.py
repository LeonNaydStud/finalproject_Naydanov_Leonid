import json
import os
from threading import Lock

class DatabaseManager:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_paths()
        return cls._instance

    def _init_paths(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.portfolios_file = os.path.join(self.data_dir, "portfolios.json")
        self.rates_file = os.path.join(self.data_dir, "rates.json")
        for f in [self.users_file, self.portfolios_file, self.rates_file]:
            if not os.path.exists(f):
                with open(f, "w", encoding="utf-8") as file:
                    json.dump([] if "users" in f or "portfolios" in f else {}, file)

    def read_json(self, filename):
        with self._lock:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)

    def write_json(self, filename, data):
        with self._lock:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
