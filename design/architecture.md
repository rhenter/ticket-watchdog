# Architecture Design for Ticket Watchdog Service

This document describes the high-level architecture, component interactions, design trade-offs, security considerations,
and future work plans for the Ticket Watchdog SLA Monitoring Service.

---

## 1. Overview

The Ticket Watchdog service continuously tracks customer-support tickets, evaluates SLA clocks, and pro-actively
escalates tickets at risk of breaching via Slack notifications and real-time WebSocket streams.

**Key components:**

- **FastAPI REST API**: Ingests ticket events and exposes query endpoints.
- **PostgreSQL**: Stores tickets, status history, and alerts data models.
- **APScheduler**: Background scheduler that triggers SLA evaluations every minute.
- **Alert Processor**: Persists alerts, updates escalation levels, sends Slack messages, and broadcasts via WebSocket.
- **Configuration Watcher**: Hot-reloads [`sla_config.yaml`](../sla_config.yaml) on changes.
- **WebSocket Manager**: Streams alert events to connected front-end clients.
- **Docker Compose / Terraform**: Container orchestration for local dev and IaC for AWS Fargate + RDS.

---

## 2. Architecture Diagram

```
       +---------+                  +---------------+                  +------------+
       | Client  |-- HTTP/REST API → |   FastAPI     |-- SQL/ORM ------→ | PostgreSQL|
       +---------+                  +---------------+                  +------------+
                                         |        ^
                                         |        |
                                         v        |
                                   +------------+|
                                   | Scheduler  ||
                                   | (APScheduler)
                                   +------------+|
                                         |
                        +----------------+----------------+
                        |                                 |
                        v                                 v
               +----------------+                 +----------------+
               | Slack Webhook  |                 | WebSocket Hub  |
               +----------------+                 +----------------+
```

---

## 3. Component Interactions

1. **Ticket Ingestion** (`POST /tickets`)
    - Accepts a batch of `TicketEvent` payloads (id, priority, timestamps, status, tier).
    - Uses idempotency (`id` + `updated_at`) to create or update ticket and history.

2. **Scheduler**
    - Runs `evaluate_slas()` every minute (configurable via `SCHEDULER_INTERVAL_MINUTES`).
    - Computes elapsed vs. target SLA times (response & resolution).
    - Calls `process_alert()` for alerts (≤ 85%) and breaches (≥ 100%).

3. **Alert Processing**
    - Persists `Alert` record and increments `escalation_level`.
    - Sends structured JSON message to Slack webhook.
    - Broadcasts event over WebSocket to subscribed clients.

4. **Configuration Watcher**
    - Monitors [`sla_config.yaml`](../sla_config.yaml) with Watchdog and hot-reloads settings without restart.

5. **Query & Dashboard**
    - `GET /tickets/{id}` returns current SLA status, remaining times, escalation level, history, and alerts.
    - `GET /dashboard` supports pagination (`offset`/`limit`) and filtering by SLA state (`ok`, `alert`, `breach`).

---

## 4. Design Trade-offs

| Decision                 | Options                           | Chosen & Rationale                                                          |
|--------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| **REST Framework**       | Django REST Framework vs FastAPI  | **FastAPI**: high performance, built-in Pydantic validation, async support  |
| **Background Scheduler** | Celery vs APScheduler             | **APScheduler**: lightweight, integrated in same process, easier testing    |
| **Database**             | PostgreSQL vs NoSQL               | **PostgreSQL**: ACID, relational history queries, JSON support              |
| **WebSocket Layer**      | Socket.IO vs native WebSocket     | **Native FastAPI WebSocket**: minimal dependencies, full ES6 client support |
| **Config Hot-reload**    | Env vars vs Watchdog              | **Watchdog**: dynamic reload without container restart                      |
| **Notifications**        | Direct API calls vs Message Queue | **Direct HTTP**: simplicity; message queue added in future improvements     |

---

## 5. Security Considerations

- **Secrets Management**: use AWS Secrets Manager (or Docker secrets locally) for database and Slack webhook
  credentials.
- **Least Privilege**: IAM role for Fargate tasks grants only access to Secrets Manager and RDS.
- **Network Policies**: private subnets for RDS; public API via Application Load Balancer.
- **Data Validation**: Pydantic schemas enforce strict payload contracts.
- **Logging & Auditing**: structured JSON logs with correlation IDs for tracing.

---

## 6. Observability & Monitoring

- **Structured Logging**: JSON with `correlation_id`, `ticket_id`, `operation`, and `latency_ms`.
- **Metrics**: Future integration with Prometheus/Grafana for:
    - Request latency
    - Scheduler job duration
    - SLA breach counts
- **Tracing**: optional OpenTelemetry integration for distributed traces.

---

## 7. Testing & Quality Assurance

- **Automated Tests**: Comprehensive unit and integration tests using pytest.
- **Continuous Integration**: GitHub Actions workflow runs tests and uploads coverage to Codecov on every push.
- **Coverage**: Codecov badge in the main README reflects test coverage.
- **Mocking**: All external dependencies (Slack, WebSocket) are mocked in tests for reliability.

---

## 8. API Versioning & Extensibility

- **Versioning**: The API is currently unversioned, but can be extended with `/v1/`, `/v2/`, etc. in the future.
- **Extensibility**: Modular design allows for easy addition of new endpoints, notification channels, or storage backends.

---

## 9. Glossary

- **SLA**: Service Level Agreement, a contractually defined response/resolution time for support tickets.
- **Alert**: A notification that a ticket is approaching or has breached its SLA.
- **Escalation**: Increasing the priority or visibility of a ticket due to SLA risk or breach.
- **Idempotency**: Ensuring repeated ticket events with the same `id` and `updated_at` do not create duplicates.
- **Watchdog**: File system observer that hot-reloads configuration on changes.
- **WebSocket**: Real-time, bidirectional communication channel for streaming alerts to clients.

---

## 10. Future Work

- **High Availability**: run multiple scheduler instances with leader election (Redis lock).
- **Alert Deduplication**: suppress duplicate alerts within a configurable window.
- **Message Queue**: introduce Kafka or SQS for decoupling alert processing.
- **Rate Limiting & Throttling**: protect API and Slack from overload.
- **Enhanced Dashboard**: real-time React UI consuming WebSocket stream.
- **Deployment Automation**: CI/CD pipelines with GitHub Actions and Terraform Cloud.

---

## License

This project is licensed under the MIT License.
