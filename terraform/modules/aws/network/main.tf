# Argus — AWS network module (VPC + subnets multi-AZ para EKS/MSK/RDS).
# Complementa os módulos Azure existentes: o Argus roda o plano de dados em
# Databricks/Snowflake e os serviços de aplicação (services/) em EKS. Ver
# ADR-001 (cloud strategy) e ADR-023 (EKS).

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

variable "name" {
  type        = string
  description = "Prefixo de nome dos recursos (ex.: argus-dev)."
}

variable "cidr_block" {
  type        = string
  default     = "10.20.0.0/16"
  description = "CIDR da VPC."
}

variable "azs" {
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
  description = "AZs para as subnets."
}

variable "tags" {
  type    = map(string)
  default = {}
}

resource "aws_vpc" "this" {
  cidr_block           = var.cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(var.tags, { Name = "${var.name}-vpc" })
}

resource "aws_subnet" "private" {
  for_each          = { for idx, az in var.azs : az => idx }
  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  cidr_block        = cidrsubnet(var.cidr_block, 4, each.value)
  tags = merge(var.tags, {
    Name                              = "${var.name}-private-${each.key}"
    "kubernetes.io/role/internal-elb" = "1"
  })
}

resource "aws_subnet" "public" {
  for_each                = { for idx, az in var.azs : az => idx }
  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.key
  cidr_block              = cidrsubnet(var.cidr_block, 4, each.value + 8)
  map_public_ip_on_launch = true
  tags = merge(var.tags, {
    Name                     = "${var.name}-public-${each.key}"
    "kubernetes.io/role/elb" = "1"
  })
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "private_subnet_ids" {
  value = [for s in aws_subnet.private : s.id]
}

output "public_subnet_ids" {
  value = [for s in aws_subnet.public : s.id]
}
