# TF notes
# enable container registry
# enable cloud run
# enable cloud scheduler
# enable secrets manager
# create SA (see https://benjamincongdon.me/blog/2019/11/21/Setting-up-Cloud-Scheduler-to-Trigger-Cloud-Run/)
# create secrets
# give secrets access to cloud run,
# give invoke to SA

# Enable APIs
# enable container registry
# enable cloud run
# enable cloud scheduler
# enable secrets manager

locals {
    apis = [
        "run.googleapis.com",
        "containerregistry.googleapis.com",
        "secretmanager.googleapis.com",
        "cloudscheduler.googleapis.com",
  ]
}

resource "google_project_service" "api" {
  for_each = toset(local.apis)
  project  = var.project
  service  = each.key
}
