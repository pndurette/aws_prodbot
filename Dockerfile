FROM python:3-slim-buster

# Install Poetry to install the rest
RUN pip install poetry

# Copy files
COPY src /app
WORKDIR /app

# Install depandancies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

# Install NLTK data
RUN python -m nltk.downloader punkt averaged_perceptron_tagger -d /usr/local/share/nltk_data

# Run app with 'aws.json' service data
ENTRYPOINT [ "python", "app.py", "aws.json" ]