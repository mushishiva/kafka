"""
Заблокировать пользователя 2 для пользователя 1:
python -m blocker --action block --from-user 1 --to-user 2

Разблокировать пользователя 2 для пользователя 1:
python -m blocker --action unblock --from-user 1 --to-user 2
"""

import argparse
import json
from dataclasses import asdict, dataclass
from enum import StrEnum

from base import BLOCKED_USERS_TOPIC, base_conf
from confluent_kafka import Producer


# DTO для события блокировки/разблокировки
class Action(StrEnum):
    BLOCK = "block"
    UNBLOCK = "unblock"


@dataclass
class BlockEvent:
    from_user: int
    to_user: int
    action: Action

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode()

    @classmethod
    def from_json(cls, json_str: bytes) -> "BlockEvent":
        data = json.loads(json_str)
        data["action"] = Action(data["action"])
        return cls(**data)


# Функция для парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action",
        choices=list(Action),
        required=True,
        help="Действие блокировки/разблокировки",
    )
    parser.add_argument(
        "--from-user",
        type=int,
        required=True,
        help="ID пользователя, который блокирует",
    )
    parser.add_argument(
        "--to-user",
        type=int,
        required=True,
        help="ID пользователя, которого блокируют",
    )
    return parser.parse_args()


# Функция для отправки события блокировки/разблокировки
def main() -> None:
    args = parse_args()
    producer = Producer(base_conf)
    event = BlockEvent(
        from_user=args.from_user,
        to_user=args.to_user,
        action=Action(args.action),
    )
    producer.produce(topic=BLOCKED_USERS_TOPIC, value=event.to_json())
    producer.flush()


if __name__ == "__main__":
    main()
