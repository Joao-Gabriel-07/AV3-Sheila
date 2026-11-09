output "postgresql_service_uri" {
  value     = aiven_pg.postgres.service_uri
  sensitive = true
}
