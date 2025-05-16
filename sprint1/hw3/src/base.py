import os
import sys
from typing import Any, Final, cast

from confluent_kafka import KafkaError, Message
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer, AvroSerializer
from confluent_kafka.serialization import MessageField, SerializationContext
from faust.serializers import Codec


class Std:
    @staticmethod
    def info(message: str) -> None:
        sys.stdout.write(f"[DEBUG]: {message}\n")

    @staticmethod
    def error(message: str) -> None:
        sys.stderr.write(f"[ERROR]: {message}\n")


ConfigDict = dict[str, Any]

# Объявление констант
KAFKA_BOOTSTRAP_SERVERS: Final[str] = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "PLAINTEXT://kafka:9092")
MESSAGES_TOPIC: Final[str] = os.environ.get("HW_INPUT_MESSAGES_TOPIC", "messages")
FILTERED_MESSAGES_TOPIC: Final[str] = os.environ.get("HW_FILTERED_MESSAGES_TOPIC", "filtered_messages")
BLOCKED_USERS_TOPIC: Final[str] = os.environ.get("HW_BLOCKED_USERS_TOPIC", "blocked_users")
SCHEMA_REGISTRY_URL: Final[str] = os.environ.get("KAFKA_SCHEMA_REGISTRY_URL", "")

# Конфигурация
base_conf: ConfigDict = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,  # Адрес брокера Kafka
}


def init_kafka() -> None:
    """
    Инициализация kafka. Создание топиков если они не существуют.
    """

    # Создаем объект админа для манипуляций с kafka
    admin = AdminClient(base_conf)

    # Создаем нужные нам топики: messages, filtered_messages, blocked_users
    list_topics = [MESSAGES_TOPIC, FILTERED_MESSAGES_TOPIC, BLOCKED_USERS_TOPIC]
    topics = {
        topic_name: NewTopic(
            topic_name,
            num_partitions=1,
            replication_factor=1,
        )
        for topic_name in list_topics
    }

    # Берем все уже существующие топики из kafka, фильтруем и добавляем
    # только те, которые не существуют
    metadata = admin.list_topics()
    new_topics = [
        topics[topic_name]
        for topic_name in metadata.topics.keys()
        if topic_name not in list_topics and topic_name in topics
    ]

    if new_topics:
        futures = admin.create_topics(new_topics)
        for topic_name, future in futures.items():
            try:
                future.result()
            except Exception as e:
                Std.error(f"Ошибка при создании топика '{topic_name}': {e}")


def load_schema(schema_file: str) -> str:
    with open(schema_file) as fd:
        return fd.read()


message_schema = load_schema("message_schema.json")
schema_registry_conf = {"url": SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
serializer = AvroSerializer(schema_registry_client, message_schema)
deserializer = AvroDeserializer(schema_registry_client, message_schema)


class AvroCodec(Codec):
    def __init__(self, serializer: AvroSerializer, deserializer: AvroDeserializer) -> None:
        self.serializer = serializer
        self.deserializer = deserializer
        self.ctx = SerializationContext("", MessageField.VALUE)

    def dumps(self, data: dict) -> bytes:
        return cast(bytes, self.serializer(data, self.ctx))

    def loads(self, data: bytes) -> dict:
        return cast(dict, self.deserializer(data, self.ctx))


# Регистрируем наш сериализатор
avro_codec = AvroCodec(serializer, deserializer)

# Конфигурация для чтения и записи сообщений
read_conf: ConfigDict = {
    "auto.offset.reset": "earliest",  # Начало чтения с самого начала
    "enable.auto.commit": True,  # Автоматический коммит смещений,
    "value.deserializer": deserializer,  # Десериализатор для значений
}
write_conf: ConfigDict = {
    "value.serializer": serializer,  # Сериализатор для значений
}

read_conf.update(base_conf)
write_conf.update(base_conf)


# Функция обратного вызова для подтверждения доставки
def delivery_report(err: KafkaError | None, msg: Message) -> None:
    if err is not None:
        Std.info(f"Не удалось доставить сообщение: {err}")
    else:
        ctx = SerializationContext(msg.topic(), MessageField.VALUE)  # type: ignore
        data = deserializer(msg.value(), ctx)  # type: ignore
        Std.info(f"Сообщение доставленно в топик '{msg.topic()}' [{msg.partition()}]: {str(data)}")
