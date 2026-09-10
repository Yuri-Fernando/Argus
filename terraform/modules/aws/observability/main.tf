# Argus — observability module: workspace Prometheus gerenciado (AMP) +
# grupo de logs. Traces vão para o backend OTLP configurado no ambiente.
# Ver system-design/12-observability.md.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

variable "name" { type = string }
variable "log_retention_days" {
  type    = number
  default = 30
}
variable "tags" {
  type    = map(string)
  default = {}
}

resource "aws_prometheus_workspace" "this" {
  alias = "${var.name}-amp"
  tags  = var.tags
}

resource "aws_cloudwatch_log_group" "platform" {
  name              = "/argus/${var.name}/platform"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

output "prometheus_endpoint" {
  value = aws_prometheus_workspace.this.prometheus_endpoint
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.platform.name
}
