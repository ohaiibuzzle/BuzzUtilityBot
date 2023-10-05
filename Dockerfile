FROM python:3.9-bullseye AS wheel_builder
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential 

COPY requirements.txt /tmp/requirements.txt
RUN pip wheel -r /tmp/requirements.txt --wheel-dir /tmp/wheels


FROM python:3.9-slim-bullseye

# Install OS deps
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
COPY --from=wheel_builder /tmp/wheels /tmp/wheels
RUN pip install --no-index --find-links=/tmp/wheels -r /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN rm -rf /tmp/wheels

RUN mkdir -p /app/src
COPY src/ /app/src

VOLUME /app/runtime
WORKDIR /app

CMD ["python", "src/main.py"]
