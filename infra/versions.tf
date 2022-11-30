terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0.0"
    }
  }
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "pierrenick"

    workspaces {
      name = "bot_aws"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}