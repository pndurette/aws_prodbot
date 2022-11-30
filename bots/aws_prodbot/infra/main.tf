# TF notes
# create SA (see https://benjamincongdon.me/blog/2019/11/21/Setting-up-Cloud-Scheduler-to-Trigger-Cloud-Run/)
# create secrets
# give secrets access to cloud run,
# give invoke to SA


/*
Required services:

    gcloud services enable \
        run.googleapis.com \
        artifactregistry.googleapis.com \
        secretmanager.googleapis.com \
        cloudscheduler.googleapis.com

*/

resource "google_artifact_registry_repository" "registry" {
  provider = google-beta

  repository_id = var.bot_name
  location      = var.region
  format        = "DOCKER"
}

# API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET

/*

gcloud beta run deploy aws-prodbot \
--image=gcr.io/twitter-bots-pnd/aws-prodbot@sha256:29b1c230c46969c7ba64e5f533befbc71c98f5545a986025276a4b3ec03c1212 \
--platform=managed \
--region=northamerica-northeast1 \
--project=twitter-bots-pnd \
--memory=128Mi \
--set-env-vars AWS_PRODUCTS_FILE=aws.json \
--set-secrets API_KEY=aws-prodbot-API_KEY:latest,API_SECRET=aws-prodbot-API_SECRET:latest,ACCESS_TOKEN=aws-prodbot-ACCESS_TOKEN:latest,ACCESS_TOKEN_SECRET=aws-prodbot-ACCESS_TOKEN_SECRET:latest

gcloud beta run deploy aws-prodbot \
--image=gcr.io/twitter-bots-pnd/aws-prodbot:latest@sha256:7d6a3768a5dd1964577d78663eac141b1ed714ede2fe40810d55e8402d76f28b \
--platform=managed \
--region=northamerica-northeast1 \
--project=twitter-bots-pnd \
--memory=128Mi \
--set-env-vars AWS_PRODUCTS_FILE=aws.json \
--set-secrets API_KEY=aws-prodbot-API_KEY:latest,API_SECRET=aws-prodbot-API_SECRET:latest,ACCESS_TOKEN=aws-prodbot-ACCESS_TOKEN:latest,ACCESS_TOKEN_SECRET=aws-prodbot-ACCESS_TOKEN_SECRET:latest


*/