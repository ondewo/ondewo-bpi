# test runner when you need ubuntu installs
FROM ubuntu:24.04 AS ubuntu_test_runner

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y <installs>
# /ubuntu


# test runner for when you dont
FROM python:3.12-slim AS python_test_runner
# /python


# choose either the python one or the ubuntu one.
#FROM <choice (ubuntu_test_runner or python_test_runner)>

# Delete all this if you dont want a pypi mirror
ENV HOST_IP=172.17.0.1
ENV LOCAL_MIRROR=http://"$HOST_IP":/3141/root/pypi/+simple/

RUN pip3 install -U pip
RUN echo [global] >> /etc/pip.conf && \
    echo index-url = http://$HOST_IP:3141/root/pypi/+simple/ >> /etc/pip.conf && \
    echo [install] >> /etc/pip.conf && \
    echo trusted-host = $HOST_IP >> /etc/pip.conf && \
    echo "              pypi.org" >> /etc/pip.conf && \
    echo extra-index-url = https://pypi.org/simple/ >> /etc/pip.conf && \
    echo no-cache-dir = true >> /etc/pip.conf && \
    echo timeout = 100 >> /etc/pip.conf && \
    cat /etc/pip.conf
#/ pypi mirror

WORKDIR /tmp/transfer

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

CMD python3 -m pytest -vv --capture=no --junit-xml=log/"$RESULTS" "$TESTFILE"
