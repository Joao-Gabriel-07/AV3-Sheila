resource "aiven_pg" "postgres" {
  project      = var.project_name
  service_name = "banco-mortalidade-materna"
  plan         = "free-1-1gb"
  cloud_name   = "do-sfo"
}
