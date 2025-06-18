# Ticket Watchdog Terraform Infrastructure

This directory contains Terraform scripts to provision the cloud infrastructure for the Ticket Watchdog project.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) v1.0+
- AWS CLI configured with appropriate credentials
- Docker image for the API built and pushed to a registry (e.g., Docker Hub, ECR)

## Setup & Usage

1. **Initialize Terraform**

```bash
terraform init
```

2. **Review and Edit Variables**

Edit `variables.tf` or provide variables via CLI or a `.tfvars` file. Required variables:
- `aws_region` (e.g., us-east-1)
- `docker_image` (e.g., your-docker-image:latest)
- `db_user`, `db_password`, `db_name`, `db_port`
- `slack_webhook_url`
- `subnets` (list of subnet IDs)
- `security_groups` (list of security group IDs)

Example `terraform.tfvars`:
```hcl
aws_region        = "us-east-1"
docker_image      = "your-docker-image:latest"
db_user           = "user"
db_password       = "pass"
db_name           = "sla_db"
db_port           = 5432
slack_webhook_url = "https://hooks.slack.com/..."
subnets           = ["subnet-abc123"]
security_groups   = ["sg-abc123"]
```

3. **Plan the Deployment**

```bash
terraform plan -var-file=terraform.tfvars
```

4. **Apply the Infrastructure**

```bash
terraform apply -var-file=terraform.tfvars
```

5. **Destroy the Infrastructure (when needed)**

```bash
terraform destroy -var-file=terraform.tfvars
```

## Resources Provisioned
- AWS ECS Fargate cluster and service
- Amazon Aurora PostgreSQL cluster
- AWS Secrets Manager for DB credentials
- ECS task definition for the API
- CloudWatch log group

---
For more details, see the main project [README](../../README.md). 