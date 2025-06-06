### Запускаем проект
- kafka: одна нода
- debezium-ui
- schema-registry
- kafka-connect
- prometheus
- grafana
- postgres
- ui
```bash
➜ git clone git@github.com:mushishiva/kafka.git
➜ cd kafka/sprint1/hw5/hw5
➜ docker-compose up --build
```

Проверяем что все контейнеры запущены (8шт)
```bash
➜ docker ps
CONTAINER ID   IMAGE                           COMMAND                  CREATED          STATUS                            PORTS                                                                                                                NAMES
6efa6d8519f6   hw5-kafka-connect               "/etc/confluent/dock…"   7 seconds ago    Up 7 seconds (health: starting)   0.0.0.0:8083->8083/tcp, :::8083->8083/tcp, 0.0.0.0:9875-9876->9875-9876/tcp, :::9875-9876->9875-9876/tcp, 9092/tcp   hw5-kafka-connect-1
499452f8d114   prom/prometheus:v2.30.3         "/bin/prometheus --w…"   32 minutes ago   Up 20 minutes                     0.0.0.0:9090->9090/tcp, :::9090->9090/tcp                                                                            hw5-prometheus-1
5128d9e503e9   bitnami/schema-registry:7.6     "/opt/bitnami/script…"   32 minutes ago   Up 20 minutes                     0.0.0.0:8081->8081/tcp, :::8081->8081/tcp                                                                            hw5-schema-registry-1
ff441be8edd2   debezium/postgres:16            "docker-entrypoint.s…"   32 minutes ago   Up 20 minutes                     0.0.0.0:5432->5432/tcp, :::5432->5432/tcp                                                                            postgres
b2601690123a   hw5-grafana                     "/run.sh"                32 minutes ago   Up 20 minutes                     0.0.0.0:3000->3000/tcp, :::3000->3000/tcp                                                                            hw5-grafana-1
50697244974e   bitnami/kafka:3.7               "/opt/bitnami/script…"   32 minutes ago   Up 20 minutes                     9092/tcp, 127.0.0.1:9094->9094/tcp                                                                                   hw5-kafka-0-1
c0320226b769   quay.io/debezium/debezium-ui    "/deployments/run-ja…"   32 minutes ago   Up 20 minutes                     0.0.0.0:8088->8080/tcp, [::]:8088->8080/tcp                                                                          hw5-debezium-ui-1
707cbc9c917d   provectuslabs/kafka-ui:v0.7.0   "/bin/sh -c 'java --…"   32 minutes ago   Up 20 minutes                     0.0.0.0:8080->8080/tcp, :::8080->8080/tcp                                                                            hw5-ui-1
```

### Подключаемся к БД
```bash
docker exec -it postgres psql -h 127.0.0.1 -U postgres-user -d customers
```

### Создаем две таблицы users и orders
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    product_name VARCHAR(100),
    quantity INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Проверяем что коннектор работает
```bash
➜ curl -s localhost:8083 | jq
{
  "version": "7.7.1-ccs",
  "commit": "91d86f33092378c89731b4a9cf1ce5db831a2b07",
  "kafka_cluster_id": "practicum"
}
```

### Смотрим список плагинов
```bash
➜ curl -s localhost:8083/connector-plugins | jq
[
  {
    "class": "io.confluent.connect.jdbc.JdbcSinkConnector",
    "type": "sink",
    "version": "10.8.4"
  },
  {
    "class": "io.confluent.connect.jdbc.JdbcSourceConnector",
    "type": "source",
    "version": "10.8.4"
  },
  {
    "class": "io.debezium.connector.postgresql.PostgresConnector",
    "type": "source",
    "version": "3.1.2.Final"
  },
  {
    "class": "org.apache.kafka.connect.mirror.MirrorCheckpointConnector",
    "type": "source",
    "version": "7.7.1-ccs"
  },
  {
    "class": "org.apache.kafka.connect.mirror.MirrorHeartbeatConnector",
    "type": "source",
    "version": "7.7.1-ccs"
  },
  {
    "class": "org.apache.kafka.connect.mirror.MirrorSourceConnector",
    "type": "source",
    "version": "7.7.1-ccs"
  }
]
```

Нас интересует `io.debezium.connector.postgresql.PostgresConnector`.

### Убеждаемся что коннекторов нет
```bash
➜ curl -s http://localhost:8083/connectors | jq
[]
```

### Создаем коннектор
```bash
➜ curl -s -X PUT -H "Content-Type: application/json" -d @kafka-connect/connector.json http://localhost:8083/connectors/pg-connector/config | jq
{
  "name": "pg-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres-user",
    "database.password": "postgres-pw",
    "database.dbname": "customers",
    "database.server.name": "customers",
    "table.whitelist": "public.users,public.orders",
    "transforms": "unwrap",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
    "transforms.unwrap.drop.tombstones": "false",
    "transforms.unwrap.delete.handling.mode": "rewrite",
    "topic.prefix": "customers",
    "topic.creation.enable": "true",
    "topic.creation.default.replication.factor": "-1",
    "topic.creation.default.partitions": "-1",
    "skipped.operations": "none",
    "name": "pg-connector"
  },
  "tasks": [],
  "type": "source"
}
```

### Смотрим что коннектор создался и таска запустилась
```bash
➜ curl -s http://localhost:8083/connectors/pg-connector/status | jq
{
  "name": "pg-connector",
  "connector": {
    "state": "RUNNING",
    "worker_id": "localhost:8083"
  },
  "tasks": [
    {
      "id": 0,
      "state": "RUNNING",
      "worker_id": "localhost:8083"
    }
  ],
  "type": "source"
}
```

Теперь можно проверить работу коннектора

### Включаем читателя
```bash
➜ docker-compose run consumer python ./consumer.py customers.public.users
```

### Создаем записи в таблице
```sql
customers=# INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com');
INSERT INTO users (name, email) VALUES ('Jane Smith', 'jane@example.com');
INSERT INTO users (name, email) VALUES ('Alice Johnson', 'alice@example.com');
INSERT INTO users (name, email) VALUES ('Bob Brown', 'bob@example.com');
INSERT 0 1
INSERT 0 1
INSERT 0 1
INSERT 0 1
```

### Смотрим в админку кафки в раздел топиков. Там создастся новый топик `customers.public.users` и приходят события на новые записи в таблице
customers - префикс который мы указали в конфиге
public - дефолтная схема pg
users - таблица
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw5/hw5/data/new_row.png"/>

### В консоле видно что сообщения были прочитаны читателем
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw5/hw5/data/terminal.png"/>

## Вторая часть ДЗ (про метрики)

### Ранее мы настраивали:
- в кафке-коннекторе JMX
- в Prometheus настроили таргет на jmx коннектора

Вот:
```
...
# Export JMX metrics to :9876/metrics for Prometheus
KAFKA_JMX_PORT: 9875
KAFKA_OPTS: -javaagent:/opt/jmx_prometheus_javaagent-0.15.0.jar=9876:/opt/kafka-connect.yml
...
```

И вот:
```
...
# Scrape Kafka Connect /metrics
- job_name: 'kafka-connect-host'
scrape_interval: 1m
scrape_timeout: 1m
static_configs:
    - targets: ['kafka-connect:9876']
...
```

### Проверим что Prometheus получает метрики из коннектора. (http://localhost:9090/targets)
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw5/hw5/data/check_prometheus.png"/>

### Посмотрим сами метрики в графане (http://localhost:3000)
Видим рабочую таску
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw5/hw5/data/g1.png"/>

### Смотрим на метрики под нагрузкой. Генерируем вставки в БД.
```sql
INSERT INTO users (name, email)
SELECT
    'Name_' || i || '_' || substring('abcdefghijklmnopqrstuvwxyz', (random() * 26)::integer + 1, 1),
    'Email_' || i || '_' || substring('abcdefghijklmnopqrstuvwxyz', (random() * 26)::integer + 1, 1)
FROM
    generate_series(1, 900000) AS i;
```

Видно что есть активность, но не все графики на дэшике работают.
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw5/hw5/data/g2.png"/>
Сами метрики есть
<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw5/hw5/data/m1.png"/>
