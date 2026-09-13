terraform {
  required_version = ">= 1.16.2, < 1.17.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "= 8.2.0"
    }
  }
}
