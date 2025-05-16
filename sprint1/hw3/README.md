### Запускаем проект
- kafka: одна нода
- ksqldb-server
- schema-registry
- ui
```bash
➜ git clone git@github.com:mushishiva/kafka.git
➜ cd kafka/sprint1/hw3
➜ docker-compose up --build
```

Проверяем что все контейнеры запущены (4шт)
```bash
➜ docker ps
CONTAINER ID   IMAGE                                    COMMAND                  CREATED          STATUS          PORTS      NAMES
8f4a431161cf   bitnami/kafka:3.4                        "/opt/bitnami/script…"   23 seconds ago   Up 22 seconds   9092/tcp   hw3-kafka-1
535acc9e82e2   provectuslabs/kafka-ui:v0.7.0            "/bin/sh -c java --a…"   23 seconds ago   Up 22 seconds   8080/tcp   hw3-ui-1
d6166b64f088   confluentinc/ksqldb-server:latest        "/usr/bin/docker/run"    23 seconds ago   Up 22 seconds   8088/tcp   hw3-ksqldb-server-1
1248945dbc33   confluentinc/cp-schema-registry:latest   "/etc/confluent/dock…"   23 seconds ago   Up 22 seconds   8081/tcp   hw3-schema-registry-1
```

### Запускаем агента
```bash
➜ docker-compose run kafka_py python -m faust -A agent worker -l info
[2025-05-16 16:35:23,200] [1] [INFO] [^Worker]: Ready
```

### Запускаем имитацию пользователей
```bash
➜ docker-compose run kafka_py python -m user
[DEBUG]: Запуск тестовых пользователей
[DEBUG]: User(1) запущен
[DEBUG]: User(3) запущен
[DEBUG]: User(2) запущен
```

Видим, что все три пользователя начинают слать сообщения друг другу и читать их.
Все нечетные сообщения маскируются звездочками (реализация цензуры через `processors`).
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw3/data/users1.png"/>

Во вкладке с агентом видим более подробную информацию о сообщениях
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw3/data/agent1.png"/>

### Блокируем пользователя
```bash
➜ docker-compose run kafka_py python -m blocker --action block --from-user 1 --to-user 2
```

Видим что пришло событие о блокировке и флаг `is_blocked` установлен в `True`
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw3/data/agent2.png"/>

Пользователь 1 больше не может писать пользователю 2
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw3/data/user2.png"/>

### Разблокируем пользователя
```bash
➜ docker-compose run kafka_py python -m blocker --action unblock --from-user 1 --to-user 2
```
