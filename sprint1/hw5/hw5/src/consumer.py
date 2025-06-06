import os
import sys
from typing import Any, Final

from confluent_kafka import Consumer

if len(sys.argv) != 2:
    print("Ожидаю один аргумент: topic")
    exit(1)

KAFKA_TOPIC: str = sys.argv[1]

ConfigDict = dict[str, Any]

KAFKA_BOOTSTRAP_SERVERS: Final[str] = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "")


# Настройка консьюмера
conf: ConfigDict = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,  # Адрес брокера Kafka
    "group.id": "consumer-group-1",  # Уникальный идентификатор группы
    "auto.offset.reset": "earliest",  # Начало чтения с самого начала
    "enable.auto.commit": True,  # Автоматический коммит смещений
    "session.timeout.ms": 6_000,  # Время ожидания активности от консьюмера
}
consumer = Consumer(conf)

# Подписка на топик
consumer.subscribe([KAFKA_TOPIC])

try:
    while True:
        msg = consumer.poll(0.1)

        if msg is None:
            continue
        if msg.error():
            print(f"Ошибка: {msg.error()}", flush=True)
            continue

        print(
            f"Получено сообщение: {str(msg.key())}, {str(msg.value())}, partition={msg.partition()}, offset={msg.offset()}",
            flush=True,
        )
finally:
    consumer.close()
