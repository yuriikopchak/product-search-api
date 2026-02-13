output "droplet_public_ip" {
  value       = digitalocean_droplet.api.ipv4_address
  description = "Public IPv4 address of the API droplet"
}

output "api_base_url" {
  value       = "http://${digitalocean_droplet.api.ipv4_address}"
  description = "Base URL of deployed API"
}

output "ssh_command" {
  value       = "ssh root@${digitalocean_droplet.api.ipv4_address}"
  description = "Command to connect to the API droplet"
}

output "database_host" {
  value       = digitalocean_database_cluster.postgres.host
  description = "Managed PostgreSQL host"
}

output "database_port" {
  value       = digitalocean_database_cluster.postgres.port
  description = "Managed PostgreSQL port"
}

output "database_name" {
  value       = digitalocean_database_db.app.name
  description = "Application database name"
}

output "database_user" {
  value       = digitalocean_database_user.app.name
  description = "Application database username"
}

output "database_password" {
  value       = digitalocean_database_user.app.password
  description = "Application database password"
  sensitive   = true
}

output "database_url" {
  value = format(
    "postgresql://%s:%s@%s:%s/%s?sslmode=require",
    digitalocean_database_user.app.name,
    urlencode(digitalocean_database_user.app.password),
    digitalocean_database_cluster.postgres.host,
    tostring(digitalocean_database_cluster.postgres.port),
    digitalocean_database_db.app.name
  )
  description = "Connection string for DATABASE_URL"
  sensitive   = true
}
