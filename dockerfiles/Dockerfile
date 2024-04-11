FROM python:3.10-slim as pybase
COPY --from=fullstorydev/grpcurl:latest /bin/grpcurl /usr/local/bin/
ENV GIT_REPO_NAME=ondewo-bpi

WORKDIR /home/ondewo/

COPY requirements.txt .
RUN \
      apt update && apt install -y git && \
      pip install -r requirements.txt && \
      apt remove -y git && \
      apt autoremove -y

COPY ondewo_bpi ondewo_bpi
COPY ondewo_bpi/example/example.env bpi.env

COPY logging.yaml .

CMD python -m ondewo_bpi.example.example

# instantiate health check
EXPOSE 50051
HEALTHCHECK --interval=1s --timeout=3s \
  CMD grpcurl -plaintext -H "" localhost:50051 list || exit 1
