variable "project" {
  description = "Short project slug (naming.md)."
  type        = string
}

variable "environment" {
  description = "dev | staging | prod."
  type        = string
}

variable "location" {
  description = "Azure region, e.g. brazilsouth."
  type        = string
}

variable "location_short" {
  description = "Short region code used in resource names, e.g. brs."
  type        = string
  default     = "brs"
}

variable "tags" {
  description = "Standard tag map from policies/tagging.tf."
  type        = map(string)
  default     = {}
}
