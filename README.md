# Ticket Watchdog

[![CI](https://github.com/rhenter/ticket-watchdog/actions/workflows/ci.yml/badge.svg)](https://github.com/rhenter/ticket-watchdog/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/rhenter/ticket-watchdog/branch/main/graph/badge.svg)](https://codecov.io/gh/rhenter/ticket-watchdog)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

## Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [API Usage](#api-usage)
- [Cloud Deployment](#cloud-deployment)
- [Design Documentation](#design-documentation)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Batch ingestion** of ticket events via `POST /tickets`
- **Persistence**: tickets, status history, and alert records in PostgreSQL
- **Background scheduler** (APScheduler) runs SLA evaluations every minute
- **Alert processor**: increments escalation level, notifies Slack, broadcasts via WebSocket
- **Configuration hot-reload**: updates SLA targets on the fly using Watchdog
- **Dashboard API**: `GET /tickets/{id}` and `GET /dashboard?offset=&limit=&state=`
- **Structured JSON logging** with correlation IDs and latency metrics
- **Docker Compose** for local development (Postgres + mock Slack + API)
- **Terraform** scripts for AWS Fargate, RDS, and Secrets Manager

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Terraform (for cloud deployment)

### Local Development

1. Clone the repository:
   Using SSH
   ```bash
   git clone git@github.com:rhenter/ticket-watchdog.git
   ```
   Using HTTPS
   ```bash
   git clone https://github.com/rhenter/ticket-watchdog.git
   cd ticket-watchdog
   ```

2. Move to the ticket-watchdog folder
   ```bash 
   cd ticket-watchdog
   ```

3. Create your .env file with the environment variables and edit according to your local settings:
   ```bash
   cp env.local .env
   ```

4. Launch services with Docker Compose:
   ```bash
   docker-compose up --build
   ```

5. Test the API:
   ```bash
   curl -X POST http://localhost:8000/tickets      -H "Content-Type: application/json"      -d '[{"id":"1","priority":"high","created_at":"2025-06-18T12:00:00Z","updated_at":"2025-06-18T12:00:00Z","status":"open","customer_tier":"gold"}]'
   ```

### Running Tests

```bash
make test
```

## Configuration

All settings are managed by environment variables and can be edited in the .env file:

- `DATABASE_URL`
- `SLACK_WEBHOOK_URL`
- `SLA_CONFIG_PATH`
- `SCHEDULER_INTERVAL_MINUTES`
- `API_HOST`
- `API_PORT`

## API Usage

### Ingest Ticket(s)
```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '[{"id":"1","priority":"high","created_at":"2025-06-18T12:00:00Z","updated_at":"2025-06-18T12:00:00Z","status":"open","customer_tier":"gold"}]'
```
**Response:**
```json
[
  {
    "id": "1",
    "priority": "high",
    "created_at": "2025-06-18T12:00:00Z",
    "updated_at": "2025-06-18T12:00:00Z",
    "status": "open",
    "customer_tier": "gold",
    "escalation_level": 0
  }
]
```

### Get Ticket by ID
```bash
curl http://localhost:8000/tickets/1
```

### Get Dashboard (all tickets)
```bash
curl http://localhost:8000/dashboard
```

### WebSocket Alerts
Connect to `ws://localhost:8000/ws/alerts` to receive real-time alert events.

## Cloud Deployment

Terraform scripts located in `infra/terraform/` provision:

- AWS ECS Fargate cluster
- Amazon Aurora PostgreSQL cluster
- AWS Secrets Manager for credentials
- ECS service with CloudWatch logs

Usage:
```bash
cd infra/terraform
terraform init
terraform apply -var-file=terraform.tfvars
```

## Design Documentation

See [design/architecture.md](design/architecture.md) for architecture details, trade-offs, and future work.

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change. Please make sure to update tests as appropriate and follow the code style guidelines.

## License
MIT © Rafael Henter

## Contact
For questions or support, open an issue or email [rafael.henter@gmail.com](mailto:rafael.henter@gmail.com).

---
