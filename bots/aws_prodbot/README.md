# AWS Prod Bot

Generate absurd-yet-plausible AWS offerings by mashing up existing products and their documentation with basic NLP, Markov Chains and by analysing current naming patterns. 

## Build

```bash
docker build . -t gcr.io/twitter-bots-pnd/aws-prodbot:latest
```

## Push

```bash
# docker push pndurette/aws-prodbot:latest
docker push gcr.io/twitter-bots-pnd/aws-prodbot:latest
```

## Run

Set `DISABLE_TWEET` to anything to only generate it but not make any attempt to tweet

### Dev

#### Local

```bash
cd src
source ../.env
# Once, import nltk data
python -m nltk.downloader punkt averaged_perceptron_tagger
python tweet.py aws.json
```

#### Docker

```bash
docker run \
	-e API_KEY="$API_KEY" \
	-e API_SECRET="$API_SECRET" \
	-e ACCESS_TOKEN="$ACCESS_TOKEN" \
	-e ACCESS_TOKEN_SECRET="$ACCESS_TOKEN_SECRET" \
    -e AWS_PRODUCTS_FILE="$AWS_PRODUCTS_FILE" \
    -p 8080:8080 \
	gcr.io/twitter-bots-pnd/aws-prodbot:latest
```

### Production (not really, but yeah)

```bash
cd src
source ../.env
flask run --host=0.0.0.0 --port 8080
```

## Misc notes

```
TF notes
enable container registry
enable cloud run
enable cloud scheduler
enable secrets manager
create SA (see https://benjamincongdon.me/blog/2019/11/21/Setting-up-Cloud-Scheduler-to-Trigger-Cloud-Run/)
create secrets
give secrets access to cloud run,
give invoke to SA
```