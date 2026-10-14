# Deribit Price Service

Сервис периодически забирает с криптобиржи Deribit текущие index price
`btc_usd` и `eth_usd`, сохраняет в PostgreSQL и отдаёт через REST API.

## Стек

- **Python 3.10**
- **FastAPI** - REST API, автоматическая OpenAPI-документация
- **SQLAlchemy 2.x (async)** + **asyncpg** - работа с PostgreSQL
- **PostgreSQL 16** - хранение цен
- **Celery** + **Redis** - периодический сбор цен каждую минуту
- **aiohttp** - асинхронный HTTP-клиент к Deribit
- **pytest** + **pytest-asyncio** + **httpx** - тесты
- **Docker** + **docker-compose** - запуск всех сервисов

## Быстрый старт

Нужен установленный Docker Desktop (или Docker + docker-compose на Linux).

```bash
# 1. Клонировать репозиторий
git clone https://gitlab.com/MN_Zer0/deribit_service.git
cd deribit-service

# 2. Создать .env из шаблона
cp .env.example .env

# 3. Поднять сервисы
docker-compose up --build -d

# 4. Дождаться готовности (20-30 секунд)
docker-compose ps

# 5. Через минуту в БД появятся первые записи
```

API: http://localhost:8000  
Swagger UI: http://localhost:8000/docs

## API

Все методы GET, обязательный query-параметр `ticker` (`btc_usd` или `eth_usd`).

### Получить все сохранённые цены по тикеру

```bash
curl "http://localhost:8000/api/v1/prices/?ticker=btc_usd"
```

Ответ:

```json
[
  {"id": 1, "ticker": "btc_usd", "price": 81563.18, "timestamp": 1792018638},
  {"id": 3, "ticker": "btc_usd", "price": 81565.57, "timestamp": 1792018698}
]
```

### Получить последнюю цену

```bash
curl "http://localhost:8000/api/v1/prices/latest?ticker=btc_usd"
```

Ответ:

```json
{"id": 5, "ticker": "btc_usd", "price": 81558.26, "timestamp": 1792018758}
```

Если для тикера нет данных, вернётся `404 {"detail": "No data for this ticker"}`.

### Получить цены с фильтром по дате

```bash
curl "http://localhost:8000/api/v1/prices/by-date?ticker=btc_usd&from_ts=1792018600&to_ts=1792018700"
```

`from_ts` и `to_ts` - UNIX timestamp, границы включительно.

### Health check

```bash
curl "http://localhost:8000/health"
# {"status": "ok"}
```

## Запуск тестов

```bash
docker-compose run --rm tests
```

Тесты работают на SQLite in-memory, поэтому продакшен-данные в PostgreSQL не
затрагиваются. Поднимать БД для тестов не нужно.

Покрытие:
- поиск последней цены по тикеру;
- поиск всех цен по тикеру;
- фильтр по диапазону дат;
- 404 для несуществующего тикера;
- 422 при отсутствии обязательного параметра `ticker`.

## Архитектура

```
┌──────────────┐      ┌───────────────┐      ┌──────────────┐
│ Celery Beat  │─────▶│ Celery Worker │─────▶│  Deribit API │
└──────────────┘      └───────┬───────┘      └──────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │  PostgreSQL   │
                      └───────▲───────┘
                              │
┌──────────────┐      ┌───────┴───────┐
│    Client    │─────▶│   FastAPI     │
└──────────────┘      └───────────────┘
```

## Структура проекта

```
app/
├── main.py                  - точка входа FastAPI, lifespan
├── config.py                - настройки из .env (pydantic-settings)
├── database.py              - engine и session factory
├── models/
│   └── price.py             - SQLAlchemy-модель Price
├── schemas/
│   └── price.py             - Pydantic-схемы
├── repositories/
│   └── price_repository.py  - доступ к БД (PriceRepository)
├── services/
│   └── price_service.py     - бизнес-логика (PriceService)
├── clients/
│   └── deribit_client.py    - aiohttp-клиент к Deribit
├── tasks/
│   ├── celery_app.py        - конфигурация Celery + beat schedule
│   └── price_tasks.py       - периодическая задача сбора цен
└── api/
    ├── dependencies.py      - DI-зависимости (сессия, сервис)
    └── v1/
        └── prices.py        - эндпоинты
```

## Design decisions

### Слоистая архитектура

Проект разбит на слои:

- **Routers** (`api/v1/prices.py`) - только HTTP: принять запрос, вызвать сервис, вернуть ответ.
- **Services** (`services/`) - бизнес-логика, оркестрация.
- **Repositories** (`repositories/`) - доступ к БД, все SQL-запросы.
- **Models** (`models/`) - SQLAlchemy-модели.
- **Schemas** (`schemas/`) - Pydantic-схемы для валидации и ответов.

Роутеры не знают про БД, сервисы не знают про HTTP, репозитории не знают про
бизнес-логику. За счёт этого сервисы легко тестировать с моком репозитория, а
компоненты можно менять независимо.

### Celery + Redis для периодических задач

Периодический сбор цен вынесен в Celery-задачу `fetch_and_save_prices`, которая
запускается через `beat_schedule` каждые 60 секунд.

Celery выбран вместо APScheduler по нескольким причинам:
- переживает перезапуск сервиса (расписание хранится в Redis);
- есть ретраи и мониторинг через Flower;
- воркеры масштабируются горизонтально;
- это стандартный инструмент для фоновых задач в Python.

Beat и worker разделены: beat только отправляет задачи по расписанию, worker их
выполняет. Это позволяет масштабировать их независимо друг от друга.

### aiohttp для клиента Deribit

Клиент (`clients/deribit_client.py`) держит одну `aiohttp.ClientSession` на всё
время работы задачи.

aiohttp, а не requests, потому что:
- не блокирует event loop;
- эффективнее на параллельных запросах;
- консистентно с остальным asyncio-стеком (FastAPI, SQLAlchemy async, asyncpg).

### PostgreSQL и модель данных

Таблица `prices`:

| Колонка | Тип | Назначение |
|---|---|---|
| `id` | `BIGSERIAL` | Первичный ключ |
| `ticker` | `VARCHAR(10)` | Индекс, фильтр по тикеру |
| `price` | `NUMERIC(18, 8)` | Цена (точность важна для финансов) |
| `timestamp` | `BIGINT` | UNIX timestamp, индекс, фильтр по дате |
| `created_at` | `TIMESTAMP` | Момент записи |

`NUMERIC`, а не `FLOAT`, потому что FLOAT теряет точность на больших числах и
не подходит для финансовых данных. `NUMERIC(18, 8)` хранит ровно.

Индексы на `ticker` и `timestamp` стоят под оба типа частых запросов API.

### Асинхронность

Весь стек асинхронный: FastAPI, SQLAlchemy `AsyncSession`, `asyncpg`, `aiohttp`.

Celery-задача синхронная (стандарт для Celery), но внутри вызывает
`asyncio.run()` для работы с асинхронным кодом.

### Изоляция тестов

Тесты поднимают отдельный engine на SQLite in-memory и подменяют DI-зависимость
`get_session` через `app.dependency_overrides`. Это даёт:
- полную изоляцию от основной БД;
- быстрый прогон (0.2 сек на все тесты);
- не нужно поднимать PostgreSQL для тестов.

В модели `Price` для `id` используется `BigInteger().with_variant(Integer, "sqlite")`,
чтобы `autoincrement` работал и в PostgreSQL, и в SQLite.

## Остановка

```bash
# Остановить контейнеры
docker-compose down

# Остановить и удалить данные PostgreSQL
docker-compose down -v
```