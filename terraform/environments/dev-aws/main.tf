# Argus — ambiente dev (AWS): compõe os módulos aws/ para o plano de
# aplicação (EKS + MSK + observability). O plano de dados (Databricks /
# Snowflake) continua nos módulos azure/ e nos environments existentes.
#
# NOTA: este ambiente é REFERÊNCIA de arquitetura. `terraform apply` real
# depende de credenciais AWS e não foi executado (projeto local-first,
# ADR-010). `terraform fmt` e `validate` passam.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name" {
  type    = string
  default = "argus-dev"
}

locals {
  tags = {
    project     = "argus"
    environment = "dev"
    managed_by  = "terraform"
  }
}

module "network" {
  source     = "../../modules/aws/network"
  name       = var.name
  cidr_block = "10.20.0.0/16"
  tags       = local.tags
}

module "eks" {
  source     = "../../modules/aws/eks"
  name       = "${var.name}-eks"
  subnet_ids = module.network.private_subnet_ids
  tags       = local.tags
}

resource "aws_security_group" "msk" {
  name   = "${var.name}-msk"
  vpc_id = module.network.vpc_id
  tags   = local.tags
}

module "msk" {
  source          = "../../modules/aws/msk"
  name            = "${var.name}-msk"
  client_subnets  = module.network.private_subnet_ids
  security_groups = [aws_security_group.msk.id]
  tags            = local.tags
}

module "observability" {
  source = "../../modules/aws/observability"
  name   = var.name
  tags   = local.tags
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "kafka_brokers" {
  value = module.msk.bootstrap_brokers_tls
}
