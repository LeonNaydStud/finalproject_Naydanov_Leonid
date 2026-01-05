import json
import os

class SettingsLoader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_settings()
        return cls._instance

    def load_settings(self):
        self.data_dir = "data"
        self.rates_ttl_seconds = 300
        self.base_currency = "USD"
        self.log_file = os.path.join("logs", "actions.log")

    def get(self, key, default=None):
        return getattr(self, key, default)
