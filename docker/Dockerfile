FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv python3-pip ffmpeg ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
SHELL ["/bin/bash", "-c"]
RUN source /opt/venv/bin/activate
RUN pip install -r requirements.txt
COPY src ./src
COPY .env.example ./.env
ENV CHANNEL_IDS=@FRANCE24 POLL_INTERVAL_SEC=30 RECORDING_ROOT=/data/recordings VIDEO_QUALITY=best SEGMENT_TIME_SEC=300 LOG_FORMAT=plain METRICS_PORT=9100 API_PORT=8000
EXPOSE 9100 8000
VOLUME ["/data"]


CMD ["python3", "-m", "src.cli", "run"]
