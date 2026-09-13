terraform {
  backend "gcs" {
    bucket = "meridian-poc-ss-260913-tfstate"
    prefix = "poc"
  }
}
