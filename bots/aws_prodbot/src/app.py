import os
from logging.config import dictConfig

from flask import Flask

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)
import tweet

# Get app config via env. v.ars
AWS_PRODUCTS_FILE = os.environ.get("AWS_PRODUCTS_FILE")


if not AWS_PRODUCTS_FILE:
    raise TypeError("Check AWS prodbot file env. var: AWS_PRODUCTS_FILE")


@app.route("/")
def main():
    tweet.main(AWS_PRODUCTS_FILE)
    return "OK"


@app.route("/healthz")
def healthz():
    return "OK"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
