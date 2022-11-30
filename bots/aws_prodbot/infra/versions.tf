terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
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
  # credentials = file("~/Downloads/key.json")
  project = var.project
  region  = var.region
}

provider "google-beta" {
  # credentials = file("~/Downloads/key.json")
  project = var.project
  region  = var.region
}
