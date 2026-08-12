variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "location" {
  description = "Azure OpenAI is not available in every region — pass a supported region explicitly (e.g. eastus2)."
  type        = string
}

variable "location_short" {
  type    = string
  default = "eus2"
}

variable "resource_group_name" {
  type = string
}

variable "deployment_name" {
  description = "Maps to AZURE_OPENAI_DEPLOYMENT in .env.example."
  type        = string
  default     = "gpt-4o"
}

variable "model_name" {
  type    = string
  default = "gpt-4o"
}

variable "model_version" {
  type    = string
  default = "2024-11-20"
}

variable "capacity_tpm" {
  description = "Deployment capacity in thousands of tokens-per-minute."
  type        = number
  default     = 10
}

variable "tags" {
  type    = map(string)
  default = {}
}
