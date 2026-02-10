FROM python:3.13-slim-bookworm

# Install OS deps
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN rm -rf /tmp/wheels

RUN mkdir -p /app/src
COPY src/ /app/src

VOLUME /app/runtime
WORKDIR /app

CMD ["python", "src/main.py"]
