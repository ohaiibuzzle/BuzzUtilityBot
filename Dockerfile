FROM python:3.9-bullseye AS wheel_builder
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential git

COPY requirements.txt /tmp/requirements.txt
RUN pip wheel -r /tmp/requirements.txt --wheel-dir /tmp/wheels


FROM python:3.9-slim-bullseye

# Install OS deps
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg

COPY requirements.txt /tmp/requirements.txt
# Subsitute pnytter @ git+https://github.com/ohaiibuzzle/pnytter.git with pnytter==0.2.2
# (as we don't want to install git in the final image)
RUN sed -i 's/pnytter @ git+https:\/\/github.com\/ohaiibuzzle\/pnytter.git/pnytter==0.2.2/g' /tmp/requirements.txt

COPY --from=wheel_builder /tmp/wheels /tmp/wheels
RUN pip install --no-index --no-cache --find-links=/tmp/wheels -r /tmp/requirements.txt
RUN rm -rf /tmp/wheels

RUN mkdir -p /app/src
COPY src/ /app/src

VOLUME /app/runtime
WORKDIR /app

CMD ["python", "src/main.py"]
