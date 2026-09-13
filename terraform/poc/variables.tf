variable "project_id" {
  type        = string
  description = "GCP project ID for POC resources."
  default     = "meridian-poc-ss-260913"
}

variable "region" {
  type        = string
  description = "Primary EU region for colocated application and database resources."
  default     = "europe-west1"
}

variable "db_password" {
  type        = string
  sensitive   = true
  ephemeral   = true
  description = "Runtime-supplied POC database password; omitted from plan and state."
}

variable "third_party_api_token" {
  type        = string
  sensitive   = true
  ephemeral   = true
  description = "Runtime-supplied synthetic token; omitted from plan and state."
}

variable "db_password_wo_version" {
  type        = number
  description = "Write-only version for google_sql_user.password_wo; increment on intentional rotation."
  default     = 1
}

variable "db_secret_data_wo_version" {
  type        = string
  description = "Write-only version for database password secret_data_wo; increment on intentional rotation."
  default     = "1"
}

variable "third_party_secret_data_wo_version" {
  type        = string
  description = "Write-only version for third-party token secret_data_wo; increment on intentional rotation."
  default     = "1"
}

variable "name_prefix" {
  type        = string
  description = "Short prefix for resource names."
  default     = "meridian"
}

variable "vpc_cidr" {
  type        = string
  description = "Primary subnet CIDR."
  default     = "10.20.0.0/24"
}

variable "psa_address" {
  type        = string
  description = "Base address for the Private Services Access reserved range (deterministic)."
  default     = "10.30.0.0"
}

variable "psa_prefix_length" {
  type        = number
  description = "Prefix length for the PSA reserved range (16 => 10.30.0.0/16)."
  default     = 16
}

variable "enable_workloads" {
  type        = bool
  description = "Stage B: create Cloud Run service/job after image digest is known."
  default     = false
}

variable "enable_wif" {
  type        = bool
  description = "Create GitHub OIDC Workload Identity Federation resources."
  default     = false
}

variable "container_image" {
  type        = string
  description = "Full image reference including digest (repo@sha256:...)."
  default     = ""
}

variable "commit_sha" {
  type        = string
  description = "Git commit SHA of the source baked into the image."
  default     = "unknown"
}

variable "github_repo_id" {
  type        = string
  description = "Immutable GitHub repository ID for WIF attribute condition."
  default     = ""
}

variable "github_owner_id" {
  type        = string
  description = "Immutable GitHub owner ID (svet1i0 = 75417040)."
  default     = "75417040"
}

variable "reviewer_member" {
  type        = string
  description = "IAM member for Viewer (e.g. user:gcp-devops@comm-it.cloud). Empty skips binding."
  default     = ""
}
