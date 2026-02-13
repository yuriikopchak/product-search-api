variable "do_token" {
  description = "Digital Ocean API token"
  type        = string
  sensitive   = true
}

variable "ssh_key_fingerprint" {
  description = "SSH key fingerprint"
  type        = string
}

variable "region" {
  description = "DigitalOcean region for droplet and managed database"
  type        = string
  default     = "nyc1"
}

variable "droplet_memory_gb" {
  description = "Droplet RAM size. Allowed values: 8 or 16"
  type        = number
  default     = 8

  validation {
    condition     = contains([8, 16], var.droplet_memory_gb)
    error_message = "droplet_memory_gb must be 8 or 16."
  }
}

variable "db_cluster_name" {
  description = "Managed PostgreSQL cluster name"
  type        = string
  default     = "product-search-db"
}

variable "db_version" {
  description = "PostgreSQL major version"
  type        = string
  default     = "16"
}

variable "db_size" {
  description = "DigitalOcean managed DB node size slug"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "db_node_count" {
  description = "Number of nodes in managed DB cluster"
  type        = number
  default     = 1
}

variable "db_name" {
  description = "Application database name"
  type        = string
  default     = "catalog_db"
}

variable "db_user" {
  description = "Application database user name"
  type        = string
  default     = "app_user"
}

variable "app_repo_url" {
  description = "Git repository URL with API source code, reachable from the droplet"
  type        = string
}

variable "app_repo_branch" {
  description = "Git branch to deploy on droplet"
  type        = string
  default     = "main"
}

variable "ssh_private_key_path" {
  description = "Path to local private SSH key used by Terraform remote-exec"
  type        = string
  default     = "~/.ssh/id_ed25519"
}

variable "app_deploy_version" {
  description = "Change this value to force re-run deployment provisioner"
  type        = string
  default     = "1"
}

variable "category_ids" {
  description = "Environment variables with category IDs required by the API"
  type        = map(string)
}
