variable "project_id" {
  type        = string
  description = "GCP project ID for bootstrap resources."
  default     = "meridian-poc-ss-260913"
}

variable "region" {
  type        = string
  description = "Primary EU region for colocated POC resources."
  default     = "europe-west1"
}
