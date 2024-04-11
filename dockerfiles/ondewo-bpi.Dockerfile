FROM python:3.10-slim as pybase
COPY --from=fullstorydev/grpcurl:latest /bin/grpcurl /usr/local/bin/
ENV GIT_REPO_NAME=ondewo-bpi

WORKDIR /home/ondewo/

# install required software packages
RUN \
    apt update \
    && apt full-upgrade -y \
    && apt install -y \
        iputils-ping \
        tree \
        tmux \
        vim \
        curl \
        sed \
        wget\
        parallel \
        jq \
        ffmpeg \
        tzdata \
        locales \
    && apt autoremove -y

# install pip requirements
COPY requirements.txt .
COPY requirements-clients.txt .
RUN \
      apt install -y git  \
      && pip install -r requirements.txt \
      && pip install -r requirements-clients.txt \
      && apt remove -y git \
      && apt autoremove -y

COPY ondewo_bpi ondewo_bpi

COPY logging.yaml .

CMD python -m ondewo_bpi.example.example
