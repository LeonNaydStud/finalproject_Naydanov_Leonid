"""
Планировщик для периодического обновления курсов.
"""

import time
import threading
import schedule
import logging
from typing import Optional, Callable
from datetime import datetime

from .updater import RatesUpdater

logger = logging.getLogger(__name__)


class RatesScheduler:
    """Планировщик для автоматического обновления курсов."""

    def __init__(self, updater: Optional[RatesUpdater] = None,
                 update_interval_minutes: int = 15):
        """
        Инициализация планировщика.

        Args:
            updater: Объект для обновления курсов
            update_interval_minutes: Интервал обновления в минутах
        """
        self.updater = updater or RatesUpdater()
        self.update_interval_minutes = update_interval_minutes
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.on_update_callback: Optional[Callable] = None

    def start(self, background: bool = True):
        """
        Запускает планировщик.

        Args:
            background: Запуск в фоновом режиме
        """
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Планировщик уже запущен")
            return

        # Настраиваем расписание
        schedule.every(self.update_interval_minutes).minutes.do(self._scheduled_update)

        # Запускаем немедленное обновление при старте
        self._scheduled_update()

        if background:
            # Запускаем в отдельном потоке
            self.stop_event.clear()
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler,
                daemon=True,
                name="RatesScheduler"
            )
            self.scheduler_thread.start()
            logger.info(f"Планировщик запущен в фоновом режиме (интервал: {self.update_interval_minutes} мин)")
        else:
            # Запускаем в основном потоке
            logger.info(f"Планировщик запущен в основном потоке (интервал: {self.update_interval_minutes} мин)")
            self._run_scheduler()

    def stop(self):
        """Останавливает планировщик."""
        self.stop_event.set()
        schedule.clear()

        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            self.scheduler_thread = None

        logger.info("Планировщик остановлен")

    def _run_scheduler(self):
        """Основной цикл планировщика."""
        logger.info("Запущен цикл планировщика")

        while not self.stop_event.is_set():
            try:
                schedule.run_pending()
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")

            # Ждем 1 секунду перед следующей проверкой
            self.stop_event.wait(1)

        logger.info("Цикл планировщика завершен")

    def _scheduled_update(self):
        """Выполняет запланированное обновление."""
        logger.info("Выполняю запланированное обновление курсов...")

        try:
            start_time = time.time()
            results = self.updater.run_update()
            elapsed = time.time() - start_time

            if results['success']:
                logger.info(
                    f"Обновление завершено успешно за {elapsed:.2f} сек. "
                    f"Получено курсов: {results['total_rates']}"
                )
            else:
                logger.warning(
                    f"Обновление завершено с ошибками за {elapsed:.2f} сек. "
                    f"Получено курсов: {results['total_rates']}"
                )

            # Вызываем callback если установлен
            if self.on_update_callback:
                self.on_update_callback(results)

        except Exception as e:
            logger.error(f"Ошибка при выполнении запланированного обновления: {e}")

    def set_update_callback(self, callback: Callable):
        """
        Устанавливает callback функцию, вызываемую после каждого обновления.

        Args:
            callback: Функция, принимающая результаты обновления
        """
        self.on_update_callback = callback

    def get_next_run_time(self) -> Optional[datetime]:
        """
        Возвращает время следующего запланированного обновления.

        Returns:
            Время следующего обновления или None если планировщик не запущен
        """
        jobs = schedule.get_jobs()
        if jobs:
            return jobs[0].next_run
        return None

    def force_update(self):
        """
        Принудительно выполняет обновление курсов.

        Returns:
            Результаты обновления
        """
        logger.info("Выполняю принудительное обновление курсов...")
        return self.updater.run_update()


def run_scheduler_demo():
    """Демонстрация работы планировщика."""
    print("=== Демонстрация планировщика обновления курсов ===")

    scheduler = RatesScheduler(update_interval_minutes=1)  # 1 минута для демо

    def on_update(results):
        print(f"\nОбновление завершено: {results}")

    scheduler.set_update_callback(on_update)

    print("Запускаю планировщик (интервал: 1 минута)...")
    print("Нажмите Ctrl+C для остановки")

    try:
        scheduler.start(background=False)
    except KeyboardInterrupt:
        print("\nОстанавливаю планировщик...")
        scheduler.stop()


if __name__ == "__main__":
    run_scheduler_demo()