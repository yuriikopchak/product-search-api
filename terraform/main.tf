terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

locals {
  droplet_size_by_memory_gb = {
    8  = "c-4"
    16 = "s-4vcpu-16gb"
  }

  db_password = coalesce(
    try(digitalocean_database_user.app.password, null),
    var.db_user_password_override,
    ""
  )

  db_env_lines = join("\n", [
    "DB_HOST=${digitalocean_database_cluster.postgres.host}",
    "DB_PORT=${tostring(digitalocean_database_cluster.postgres.port)}",
    "DB_NAME=${digitalocean_database_db.app.name}",
    "DB_USER=${digitalocean_database_user.app.name}",
    "DB_PASSWORD=${local.db_password}",
    "DB_SSLMODE=require",
  ])

  category_env_lines = join("\n", [
    for key, value in var.category_ids : "${key}=${value}"
  ])
}

resource "digitalocean_droplet" "api" {
  image    = "ubuntu-24-04-x64"
  name     = "product-search-api"
  region   = var.region
  size     = local.droplet_size_by_memory_gb[var.droplet_memory_gb]
  ssh_keys = [var.ssh_key_fingerprint]
}

resource "digitalocean_database_cluster" "postgres" {
  name       = var.db_cluster_name
  engine     = "pg"
  version    = var.db_version
  size       = var.db_size
  region     = var.region
  node_count = var.db_node_count
}

resource "digitalocean_database_db" "app" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_name
}

resource "digitalocean_database_user" "app" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.db_user
}

resource "digitalocean_database_firewall" "allow_api_droplet" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "droplet"
    value = tostring(digitalocean_droplet.api.id)
  }
}

resource "digitalocean_firewall" "api" {
  name        = "product-search-api-fw"
  droplet_ids = [digitalocean_droplet.api.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

resource "null_resource" "deploy_api" {
  depends_on = [
    digitalocean_droplet.api,
    digitalocean_database_firewall.allow_api_droplet,
    digitalocean_database_db.app,
    digitalocean_database_user.app
  ]

  triggers = {
    droplet_id      = tostring(digitalocean_droplet.api.id)
    app_repo_url    = var.app_repo_url
    app_repo_branch = var.app_repo_branch
    deploy_version  = var.app_deploy_version
  }

  lifecycle {
    precondition {
      condition     = local.db_password != ""
      error_message = "Database user password is unknown. Set db_user_password_override or let Terraform create a new DB user."
    }
  }

  connection {
    type        = "ssh"
    host        = digitalocean_droplet.api.ipv4_address
    user        = "root"
    private_key = file(pathexpand(var.ssh_private_key_path))
    timeout     = "2m"
  }

  provisioner "remote-exec" {
    inline = [
      "set -eux",
      "export DEBIAN_FRONTEND=noninteractive",
      "apt-get update",
      "apt-get install -y ca-certificates curl git docker.io",
      "systemctl enable --now docker",
      "mkdir -p /opt",
      "if [ -d /opt/product-search-api/.git ]; then git -C /opt/product-search-api fetch --all --prune; git -C /opt/product-search-api checkout ${var.app_repo_branch}; git -C /opt/product-search-api reset --hard origin/${var.app_repo_branch}; else rm -rf /opt/product-search-api && git clone --depth 1 --branch ${var.app_repo_branch} ${var.app_repo_url} /opt/product-search-api; fi",
      <<-EOT
      cat > /opt/product-search-api/.env <<'ENVEOF'
      ${local.db_env_lines}
      ${local.category_env_lines}
      ENVEOF
      EOT
      ,
      "cd /opt/product-search-api",
      "docker build -t product-search-api:latest .",
      "docker rm -f product-search-api || true",
      "docker run -d --name product-search-api --restart unless-stopped -p 80:8000 --env-file /opt/product-search-api/.env product-search-api:latest"
    ]
  }
}
