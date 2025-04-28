import os
from typing import Any, Final

from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

ConfigDict = dict[str, Any]

KAFKA_BOOTSTRAP_SERVERS: Final[str] = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "")
KAFKA_TOPIC: Final[str] = os.environ.get("KAFKA_TOPIC", "")
SCHEMA_REGISTRY_ENDPOINT: Final[str] = os.environ.get("SCHEMA_REGISTRY_ENDPOINT", "")

# Конфигурация Schema Registry
schema_registry_conf = {"url": SCHEMA_REGISTRY_ENDPOINT}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Создание десериализатора
deserializer = AvroDeserializer(schema_registry_client=schema_registry_client)


# Настройка консьюмера
conf: ConfigDict = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,  # Адрес брокера Kafka
    "group.id": "consumer-group-1",  # Уникальный идентификатор группы
    "auto.offset.reset": "earliest",  # Начало чтения с самого начала
    "enable.auto.commit": True,  # Автоматический коммит смещений
    "session.timeout.ms": 6_000,  # Время ожидания активности от консьюмера
    "value.deserializer": deserializer,  # Десериализатор для значений
}
consumer = DeserializingConsumer(conf)

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
