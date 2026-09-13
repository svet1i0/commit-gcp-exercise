resource "google_compute_network" "poc" {
  name                    = "${var.name_prefix}-vpc"
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  depends_on = [google_project_service.required]
}

resource "google_compute_subnetwork" "app" {
  name          = "${var.name_prefix}-subnet"
  project       = var.project_id
  region        = var.region
  network       = google_compute_network.poc.id
  ip_cidr_range = var.vpc_cidr

  private_ip_google_access = true
}

resource "google_compute_global_address" "psa" {
  name          = "${var.name_prefix}-psa"
  project       = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  address       = var.psa_address
  prefix_length = var.psa_prefix_length
  network       = google_compute_network.poc.id
}

resource "google_service_networking_connection" "psa" {
  network                 = google_compute_network.poc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.psa.name]

  depends_on = [google_project_service.required]
}

# No VPC firewall rules in Stage A.
# Cloud Run Direct VPC egress to Cloud SQL private IP uses PSA peering;
# private-IP Cloud SQL does not use authorized_networks, and an
# allow-all-internal rule would be boilerplate without a demonstrated need.
