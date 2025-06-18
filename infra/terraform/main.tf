terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_ecs_cluster" "this" {
  name = "ticket-watchdog-cluster"
}

resource "aws_rds_cluster" "this" {
  cluster_identifier    = "ticket-watchdog-db"
  engine                = "aurora-postgresql"
  master_username       = var.db_user
  master_password       = var.db_password
  skip_final_snapshot   = true
}

resource "aws_secretsmanager_secret" "db" {
  name = "ticket-watchdog-db-secret"
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_user
    password = var.db_password
    host     = aws_rds_cluster.this.endpoint
    port     = var.db_port
    database = var.db_name
  })
}

resource "aws_ecs_task_definition" "api" {
  family                   = "ticket-watchdog-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([{
    name      = "api"
    image     = var.docker_image
    essential = true
    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
    }]
    environment = [
      {
        name  = "DATABASE_URL"
        value = aws_secretsmanager_secret_version.db.secret_string
      },
      {
        name  = "SLACK_WEBHOOK_URL"
        value = var.slack_webhook_url
      }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/ticket-watchdog"
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "ticket-watchdog-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets         = var.subnets
    security_groups = var.security_groups
  }
}
