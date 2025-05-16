import threading
from itertools import cycle
from time import sleep
from typing import Any

from base import FILTERED_MESSAGES_TOPIC, MESSAGES_TOPIC, Std, delivery_report, init_kafka, read_conf, write_conf
from confluent_kafka import DeserializingConsumer, SerializingProducer

init_kafka()

read_conf.update(**{"group.id": "consumer-user-1"})


def class_repr(obj: Any) -> str:
    return f"{obj.__class__.__name__}({obj.user_id})"


class BaseThread(threading.Thread):
    """Базовый класс для потоков записи/чтения сообщений пользователя"""

    def __init__(self, user_id: int) -> None:
        super().__init__()
        self.running = True
        self.user_id = user_id

    def stop(self) -> None:
        Std.info(f"{self} останавливается")
        self.running = False

    def __repr__(self) -> str:
        return class_repr(self)


class UserWriter(BaseThread):
    """Имитация отправки сообщений"""

    def __init__(self, user_id: int, recipients: list[int]) -> None:
        super().__init__(user_id)
        self.recipients = recipients

    def _init_producer(self) -> None:
        self.producer = SerializingProducer(write_conf)

    def run(self) -> None:
        # Инициализация продюсера
        self._init_producer()

        # В бесконечном цикле отправляем сообщения
        for iter_count, ecipient_user_id in enumerate(cycle(self.recipients)):
            message = {
                "from_user": self.user_id,
                "to_user": ecipient_user_id,
                "message": str(iter_count),
            }
            try:
                # Отправка сообщения
                self.producer.produce(
                    topic=MESSAGES_TOPIC,
                    value=message,
                    on_delivery=delivery_report,
                )

                # Ожидание завершения отправки всех сообщений
                self.producer.flush()
            except Exception as err:
                Std.error(f"Ошибка при отправке сообщения: {err}")
            finally:
                if not self.running:
                    break
                sleep(1)


class UserReader(BaseThread):
    """Имитация чтения сообщений"""

    def _init_consumer(self) -> None:
        self.consumer = DeserializingConsumer(read_conf)
        self.consumer.subscribe([FILTERED_MESSAGES_TOPIC])

    def run(self) -> None:
        # Инициализация консьюмера
        self._init_consumer()

        try:
            while self.running:
                msg = self.consumer.poll(0.1)

                if msg is None:
                    continue
                if msg.error():
                    print(f"Ошибка: {msg.error()}")
                    continue

                Std.info(
                    f"Получено сообщение: {str(msg.key())}, {str(msg.value())}, partition={msg.partition()}, offset={msg.offset()}"
                )
        finally:
            self.consumer.close()


class User(threading.Thread):
    """
    Имитация пользователя.
    Имитирует отправку и получение сообщений.
    """

    def __init__(self, user_id: int, recipients: list[int]) -> None:
        super().__init__()
        self.user_id = user_id

        self.user_writer = UserWriter(user_id, recipients)
        self.user_reader = UserReader(user_id)

    def run(self) -> None:
        self.user_writer.start()
        self.user_reader.start()

        Std.info(f"{self} запущен")

        self.user_writer.join()
        self.user_reader.join()

    def stop(self) -> None:
        Std.info(f"{self} останавливается")

        self.user_writer.stop()
        self.user_reader.stop()

    def __repr__(self) -> str:
        return class_repr(self)


if __name__ == "__main__":
    # Создаем и запускаем тестовых пользователей
    Std.info("Запуск тестовых пользователей")

    # Создаем пользователей.
    # Первый аргумент - id пользователя.
    # Второй аргумент - список id пользователей, которым он отправляет сообщения.
    user1 = User(1, [2, 3])
    user2 = User(2, [1, 3])
    user3 = User(3, [1, 2])

    user1.start()
    user2.start()
    user3.start()

    try:
        user1.join()
        user2.join()
        user3.join()
    except KeyboardInterrupt:
        user1.stop()
        user2.stop()
        user3.stop()
