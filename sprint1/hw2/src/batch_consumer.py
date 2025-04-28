import os
from typing import Any, Final

from confluent_kafka import DeserializingConsumer, Message
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

ConfigDict = dict[str, Any]

KAFKA_BOOTSTRAP_SERVERS: Final[str] = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "")
KAFKA_TOPIC: Final[str] = os.environ.get("KAFKA_TOPIC", "")
BATCH_SIZE: Final[int] = int(os.environ.get("BATCH_SIZE", "10"))
SCHEMA_REGISTRY_ENDPOINT: Final[str] = os.environ.get("SCHEMA_REGISTRY_ENDPOINT", "")

# Конфигурация Schema Registry
schema_registry_conf = {"url": SCHEMA_REGISTRY_ENDPOINT}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Создание десериализатора
deserializer = AvroDeserializer(schema_registry_client=schema_registry_client)

# Настройка консьюмера
conf: ConfigDict = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,  # Адрес брокера Kafka
    "group.id": "consumer-group-2",  # Уникальный идентификатор группы
    "auto.offset.reset": "earliest",  # Начало чтения с самого начала
    "enable.auto.commit": False,  # Автоматический коммит смещений
    "session.timeout.ms": 6_000,  # Время ожидания активности от консьюмера
    "fetch.min.bytes": 1_024,  # Минимальный объём данных для ожидания (может потребоваться подстройка)
    # "fetch.max.wait.ms": 5_000,  # Максимальное время ожидания данных (5 секунд) No such configuration property: "fetch.max.wait.ms"
    "value.deserializer": deserializer,  # Десериализатор для значений
}
consumer = DeserializingConsumer(conf)

# Подписка на топик
consumer.subscribe([KAFKA_TOPIC])


def process_message(message: Message) -> None:
    print(
        f"Обработка сообщения: "
        f"key={str(message.key())}, "
        f"value={str(message.value())}, "
        f"partition={message.partition()}, "
        f"offset={message.offset()}",
        flush=True,
    )


try:
    while True:
        messages: list[Message] = []

        msg = consumer.poll(0.1)

        # Собираем сообщения до достижения BATCH_SIZE
        while len(messages) < BATCH_SIZE:
            msg = consumer.poll(0.1)  # Таймаут poll в секундах

            if msg is None:
                continue
            if msg.error():
                print(f"Ошибка: {msg.error()}", flush=True)
                continue

            # Добавляем сообщение в пачку
            messages.append(msg)
            process_message(msg)

        if messages:
            # Коммитим оффсет после обработки пачки
            consumer.commit(asynchronous=False)
            print(f"Оффсет закоммичен для {len(messages)} сообщений", flush=True)
finally:
    consumer.close()
