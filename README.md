# Ticket Watchdog

Ticket Watchdog is a Slack- and WebSocket-enabled SLA monitoring service for customer-support tickets. It evaluates SLA response and resolution clocks, sends alerts or breaches to Slack, and streams events to connected clients in real time.

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

All settings are managed by environment variables and be edited in the .env file:

- `DATABASE_URL`
- `SLACK_WEBHOOK_URL`
- `SLA_CONFIG_PATH`
- `SCHEDULER_INTERVAL_MINUTES`
- `API_HOST`
- `API_PORT`

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
terraform apply   -var="aws_region=us-east-1"   -var="docker_image=your-docker-image:latest"   -var="db_user=user"   -var="db_password=pass"   -var="db_name=sla_db"   -var="slack_webhook_url=https://hooks.slack.com/..."   -var='subnets=["subnet-..."]'   -var='security_groups=["sg-..."]'
```

## Design Documentation

See [design/architecture.md](design/architecture.md) for architecture details, trade-offs, and future work.

---
