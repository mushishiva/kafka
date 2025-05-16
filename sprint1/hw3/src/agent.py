import faust
from base import (
    BLOCKED_USERS_TOPIC,
    FILTERED_MESSAGES_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
    MESSAGES_TOPIC,
    Std,
    avro_codec,
    init_kafka,
)
from blocker import BlockEvent

init_kafka()


class BlockEventCodec(faust.Codec):
    def dumps(self, event: BlockEvent) -> bytes:
        return event.to_json()

    def loads(self, event: bytes) -> BlockEvent:
        return BlockEvent.from_json(event)


block_event_codec = BlockEventCodec()

# Конфигурация Faust-приложения
app = faust.App(
    "simple-faust-app",
    broker=KAFKA_BOOTSTRAP_SERVERS.replace("PLAINTEXT://", ""),
    value_serializer="raw",
)

# Определение топика для входных данных
input_topic = app.topic(MESSAGES_TOPIC)
# Определение топика для выходных данных
output_topic = app.topic(FILTERED_MESSAGES_TOPIC)
# Определение топика блокировки/разблокировки пользователя
blocked_users_topic = app.topic(BLOCKED_USERS_TOPIC, value_serializer=block_event_codec)
# Таблица для хранения заблокированных пользователей
blocked_table = app.Table(
    "blocked_users_table",
    default=list,
    partitions=1,
)


def censorship(value: bytes) -> bytes:
    """Реализация маскировки данных (цензура)"""

    data = avro_codec.loads(value)

    try:
        int_value = int(data["message"])
    except ValueError:
        return value

    if int_value % 2 == 0:
        return value

    Std.info(f"Маскировка данных: {data["message"]}")

    data["message"] = "***"

    return avro_codec.dumps(data)


def filter_blocked_users(value: bytes) -> bool:
    """Фильтрация по заблокированным пользователям"""

    data = avro_codec.loads(value)
    user_is_blocked = data["to_user"] in blocked_table.get(data["from_user"], [])

    Std.info(f"Фильтрация по заблокированным пользователям: {data} (is blocked: {user_is_blocked})")

    return not user_is_blocked


# Функция, реализующая потоковую обработку данных
@app.agent(input_topic)
async def process(stream: faust.StreamT[bytes]) -> None:
    # 1. Фильтрация по заблокированным пользователям
    filtered_stream = stream.filter(filter_blocked_users)  # type: ignore
    # 2. Применение цензуры через процессор
    processed_stream = app.stream(filtered_stream, processors=[censorship])
    async for value in processed_stream:
        Std.info(f"Обработка: {avro_codec.loads(value)}")
        # Отправка обработанных данных в выходной топик
        await output_topic.send(value=value)


# Функция, реализующая потоковую обработку данных блокировки/разблокировки пользователя
@app.agent(blocked_users_topic)
async def handle_blocked_users(stream: faust.StreamT[BlockEvent]) -> None:
    async for event in stream:
        current_blocked = set(blocked_table.get(event.from_user, []))

        message = (
            f"Пользователь {event.from_user} отправил запрос '{event.action}' "
            f"относительно пользователя {event.to_user}.\n"
            f"Текущий список заблокированных пользователей: {current_blocked}"
        )

        if event.action == "block":
            current_blocked.add(event.to_user)
        else:
            current_blocked.discard(event.to_user)

        Std.info(f"{message}\nНовый список заблокированных пользователей: {current_blocked}")

        blocked_table[event.from_user] = list(current_blocked)
