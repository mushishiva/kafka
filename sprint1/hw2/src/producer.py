import os
from itertools import repeat
from time import sleep
from typing import Any, Final

from confluent_kafka import KafkaError, Message, Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import MessageField, SerializationContext

ConfigDict = dict[str, Any]

KAFKA_BOOTSTRAP_SERVERS: Final[str] = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "")
KAFKA_TOPIC: Final[str] = os.environ.get("KAFKA_TOPIC", "")
SCHEMA_REGISTRY_ENDPOINT: Final[str] = os.environ.get("SCHEMA_REGISTRY_ENDPOINT", "")

# Конфигурация продюсера – адрес сервера
conf: ConfigDict = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
}
# Создание продюсера
producer = Producer(conf)

# Конфигурация Schema Registry
schema_registry_conf = {"url": SCHEMA_REGISTRY_ENDPOINT}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Определение схемы Avro (можно также загружать из файла)
schema_str = """
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "name", "type": "string"},
    {"name": "age", "type": "int"},
    {"name": "email", "type": ["null", "string"], "default": null}
  ]
}
"""


# Создание сериализатора
serializer = AvroSerializer(schema_registry_client, schema_str)


# Функция обратного вызова для подтверждения доставки
def delivery_report(err: KafkaError | None, msg: Message) -> None:
    if err is not None:
        print(f"Message delivery failed: {err}", flush=True)
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]: {str(msg.value())}", flush=True)


ctx = SerializationContext(KAFKA_TOPIC, MessageField.VALUE)

for iter_count, _ in enumerate(repeat(1)):
    try:
        # Пример данных для сериализации
        user_data = {
            "name": f"John Doe {iter_count}",
            "age": iter_count,
            "email": f"john.doe.{iter_count}@example.com",
        }

        # Сериализация данных
        serialized_data = serializer(user_data, ctx)
        print(f"Сериализованные данные: {str(serialized_data)}")

        # Отправка сообщения
        producer.produce(
            topic=KAFKA_TOPIC,
            value=serialized_data,
            on_delivery=delivery_report,
        )
        # Ожидание завершения отправки всех сообщений
        producer.flush()
    except Exception as err:
        print(f"Error: {err}", flush=True)
    finally:
        sleep(0.5)
