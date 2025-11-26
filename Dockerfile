FROM n8nio/n8n:latest

USER root

# Install Python & pip on Alpine
RUN apk add --no-cache python3 py3-pip

# Install instaloader (override PEP 668 "externally managed" warning)
RUN pip3 install --no-cache-dir --break-system-packages instaloader

# Working directory for insta downloads
WORKDIR /data

# Copy your script
COPY insta-extractor.py /scripts/insta-extractor.py

RUN chmod +x /scripts/insta-extractor.py && \
    chown -R node:node /data /scripts

USER node