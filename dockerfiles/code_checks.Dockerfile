FROM registry-dev.ondewo.com:5000/python/python:3.7-slim

RUN apt update && apt install make
RUN pip install flake8 mypy

RUN mkdir code_to_test

WORKDIR code_to_test

COPY ondewo_bpi ondewo_bpi
RUN rm -rf ondewo_bpi/autocoded
COPY ondewo_bpi_sip ondewo_bpi_sip
COPY ondewo_bpi_qa ondewo_bpi_qa
COPY dockerfiles/code_checks .
