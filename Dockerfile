FROM python:3.13-bookworm AS wheel_builder
RUN apt-get update && apt-get install -y build-essential git

COPY requirements.txt /tmp/requirements.txt
RUN pip wheel -r /tmp/requirements.txt --wheel-dir /tmp/wheels


FROM python:3.13-slim-bookworm

# Install OS deps
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg

COPY requirements.txt /tmp/requirements.txt

COPY --from=wheel_builder /tmp/wheels /tmp/wheels
RUN pip install --no-index --no-cache --find-links=/tmp/wheels -r /tmp/requirements.txt
RUN rm -rf /tmp/wheels

RUN mkdir -p /app/src
COPY src/ /app/src

VOLUME /app/runtime
WORKDIR /app

CMD ["python", "src/main.py"]
