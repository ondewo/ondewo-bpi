# install grpcurl for grpc health check
FROM ubuntu:20.04 as lux_base

ARG DEBIAN_FRONTEND=noninteractive

# install grpcurl
# docker.io needed for 'go get'
RUN apt update && apt install -y docker.io && apt install -y golang
RUN go get github.com/fullstorydev/grpcurl/...
RUN go install github.com/fullstorydev/grpcurl/cmd/grpcurl

# install server
FROM python:3.7-slim as pybase
COPY --from=lux_base /root/go/bin/ /usr/local/bin/
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
