variable "aws_region" {
  type = string
}

variable "docker_image" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_port" {
  type    = number
  default = 5432
}

variable "slack_webhook_url" {
  type = string
}

variable "subnets" {
  type = list(string)
}

variable "security_groups" {
  type = list(string)
}
