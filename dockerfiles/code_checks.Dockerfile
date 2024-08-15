FROM python:3.12-slim

RUN apt update && apt install make

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY requirements-static-code-checks.txt .
RUN pip install -r requirements-static-code-checks.txt

RUN mkdir code_to_test
WORKDIR code_to_test

COPY ondewo_bpi ondewo_bpi
RUN rm -rf ondewo_bpi/autocoded
# COPY ondewo_bpi_sip ondewo_bpi_sip
COPY ondewo_bpi_qa ondewo_bpi_qa
COPY dockerfiles/code_checks .
