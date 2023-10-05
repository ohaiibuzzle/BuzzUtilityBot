FROM python:3.9-bullseye AS wheel_builder
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential git

COPY requirements.txt /tmp/requirements.txt
RUN pip wheel -r /tmp/requirements.txt --wheel-dir /tmp/wheels


FROM python:3.9-slim-bullseye

# Install OS deps
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg git

COPY requirements.txt /tmp/requirements.txt
COPY --from=wheel_builder /tmp/wheels /tmp/wheels
RUN pip install --no-index --no-cache --find-links=/tmp/wheels -r /tmp/requirements.txt
RUN rm -rf /tmp/wheels && apt autoremove -y git && apt-get clean

RUN mkdir -p /app/src
COPY src/ /app/src

VOLUME /app/runtime
WORKDIR /app

CMD ["python", "src/main.py"]
