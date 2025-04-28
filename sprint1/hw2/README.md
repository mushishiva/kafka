### Запускаем проект
- кластер 3x ноды
- ui
- schema-registry
- производитель
- 2x одиночных потребителя
- 2x batch-потребителя
```bash
➜ git clone git@github.com:mushishiva/kafka.git
➜ cd kafka/sprint1/hw2
➜ docker-compose up --build producer single_consumer batch_consumer
```

Проверяем что все контейнеры запущены (10шт)
```bash
➜ docker ps
CONTAINER ID   IMAGE                                    COMMAND                  CREATED          STATUS          PORTS                                                 NAMES
bfd01b53e640   kafka-py                                 "python single_consu…"   29 minutes ago   Up 8 seconds                                                          hw2-single_consumer-2
6f31b0317d79   kafka-py                                 "python batch_consum…"   29 minutes ago   Up 8 seconds                                                          hw2-batch_consumer-2
3cbbb4cc38bf   kafka-py                                 "python single_consu…"   29 minutes ago   Up 7 seconds                                                          hw2-single_consumer-1
bd0baaba8c44   kafka-py                                 "python batch_consum…"   29 minutes ago   Up 7 seconds                                                          hw2-batch_consumer-1
af2e2f3eda03   kafka-py                                 "python producer.py"     29 minutes ago   Up 8 seconds                                                          hw2-producer-1
c9155ff7e1b2   confluentinc/cp-schema-registry:latest   "/etc/confluent/dock…"   3 hours ago      Up 8 seconds    0.0.0.0:8081->8081/tcp, :::8081->8081/tcp             hw2-schema-registry-1
b342dc4f8b68   provectuslabs/kafka-ui:v0.7.0            "/bin/sh -c 'java --…"   3 hours ago      Up 8 seconds    0.0.0.0:8080->8080/tcp, :::8080->8080/tcp             hw2-ui-1
f52d0888d55f   bitnami/kafka:3.4                        "/opt/bitnami/script…"   3 hours ago      Up 14 minutes   9092/tcp, 0.0.0.0:9095->9095/tcp, :::9095->9095/tcp   hw2-kafka-1-1
6e0dac9605b2   bitnami/kafka:3.4                        "/opt/bitnami/script…"   3 hours ago      Up 14 minutes   9092/tcp, 0.0.0.0:9094->9094/tcp, :::9094->9094/tcp   hw2-kafka-0-1
a53ccc2fad38   bitnami/kafka:3.4                        "/opt/bitnami/script…"   3 hours ago      Up 14 minutes   9092/tcp, 0.0.0.0:9096->9096/tcp, :::9096->9096/tcp   hw2-kafka-2-1
```

### Смотрим текущий список тем
Должны быть две технические темы:
- `__consumer_offsets` - метаданные смещений потребителей
- `_schemas` - метаданные схем
```bash
➜ docker-compose exec kafka-0 kafka-topics.sh --bootstrap-server localhost:9092 --list
__consumer_offsets
_schemas
```

### Создаем новую тему
Создаем тему с 3 разделами и 2 репликами
```bash
➜ docker-compose exec kafka-0 kafka-topics.sh --bootstrap-server localhost:9092 --create --topic my-topic --partitions 3 --replication-factor 2
Created topic my-topic.
```

Проверям конфигурацию созданной темы
```bash
➜ docker-compose exec kafka-0 kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic my-topic
Topic: my-topic	TopicId: xeS8gEz4RwOx_f0HH1GDUQ	PartitionCount: 3	ReplicationFactor: 2	Configs:
	Topic: my-topic	Partition: 0	Leader: 0	Replicas: 0,1	Isr: 0,1
	Topic: my-topic	Partition: 1	Leader: 1	Replicas: 1,2	Isr: 1,2
	Topic: my-topic	Partition: 2	Leader: 2	Replicas: 2,0	Isr: 2,0
```

### Результат
- консьюмеры работают параллельно и считывают одни и те же сообщения
- каждый консьюмер запущен в двух экземплярах
- есть сериализация и десериализация сообщений

<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw2/data/img1.png"/>

Схема записана в registry [http://localhost:8081/schemas](http://localhost:8081/schemas)

<img src="https://github.com/mushishiva/kafka/blob/master/sprint1/hw2/data/img2.png"/>
