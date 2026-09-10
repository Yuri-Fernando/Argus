# Argus — MSK module (Kafka gerenciado, 3 brokers multi-AZ).
# Event backbone da plataforma (ADR-019). replication.factor=3,
# min.insync.replicas=2 para durabilidade (system-design/08).

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
variable "kafka_version" {
  type    = string
  default = "3.6.0"
}
variable "broker_count" {
  type    = number
  default = 3
}
variable "broker_instance_type" {
  type    = string
  default = "kafka.m5.large"
}
variable "client_subnets" { type = list(string) }
variable "security_groups" { type = list(string) }
variable "tags" {
  type    = map(string)
  default = {}
}

resource "aws_msk_configuration" "this" {
  name           = "${var.name}-config"
  kafka_versions = [var.kafka_version]

  server_properties = <<-PROPS
    auto.create.topics.enable=false
    default.replication.factor=3
    min.insync.replicas=2
    num.partitions=12
    log.retention.hours=168
  PROPS
}

resource "aws_msk_cluster" "this" {
  cluster_name           = var.name
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.broker_count

  broker_node_group_info {
    instance_type   = var.broker_instance_type
    client_subnets  = var.client_subnets
    security_groups = var.security_groups

    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.this.arn
    revision = aws_msk_configuration.this.latest_revision
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  tags = var.tags
}

output "bootstrap_brokers_tls" {
  value = aws_msk_cluster.this.bootstrap_brokers_tls
}
