FROM python:3.9-slim-bullseye

# Install OS deps
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt --extra-index-url https://www.piwheels.org/simple

RUN mkdir -p /app/src
COPY src/ /app/src

VOLUME /app/runtime
WORKDIR /app

CMD ["python", "src/main.py"]
