FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update -y && \
  apt-get install --no-install-recommends -y -q \
  git libpq-dev build-essential libsnappy-dev && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG PROJECT_NAME=pipeline
ARG MAGE_CODE_PATH=/app
ARG USER_CODE_PATH=${MAGE_CODE_PATH}/${PROJECT_NAME}

# WORKDIR ${MAGE_CODE_PATH}

COPY ${PROJECT_NAME} ${PROJECT_NAME}

ENV USER_CODE_PATH=${USER_CODE_PATH}

# Install custom Python libraries and dependencies for your project.
# RUN pip3 install --no-cache-dir "git+https://github.com/mage-ai/mage-ai.git@td--create_blocks_tmp3#egg=mage-ai[all]"

ENV PYTHONPATH="${PYTHONPATH}:${MAGE_CODE_PATH}/${PROJECT_NAME}"
COPY script/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# CMD ["/bin/sh", "-c", "/app/run_app.sh"]
ENTRYPOINT [ "/entrypoint.sh" ]
