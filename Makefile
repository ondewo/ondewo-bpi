ENV ?= example
-include envs/${ENV}.env
export

CODE_CHECK_IMAGE=code_check_image
TEST_IMAGE=test_image
DOCKER_REGISTRY=registry-dev.ondewo.com:5000
ONDEWO_NAMESPACE=ondewo
RELEASE_VERSION=$(shell cat ondewo_bpi/version.py | sed "s:__version__ = '::"  | sed "s:'::")

########################################################
### --- Setup developer environment              --- ###
########################################################
DOCKER=/usr/bin/docker
FIND=/usr/bin/find
TIME_STAMP:=$(shell /bin/date "+%Y-%m-%d_%H:%M:%S")
SHORT_TIMESTAMP:=$(shell /bin/date "+%Y-%m-%d_%H:%M")
SHELL=/bin/bash

help: ## print usage info about help targets
	# (first comment after target starting with double ##)
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

setup_developer_environment_locally:  install_apt install_precommit_hooks install_pip_requirements install_submodules

install_apt: ## Installs apt packages for the operating system
	@echo "Nothing to install on operating system level"

install_pip_requirements: ## Installs required pip packages
	pip install -r requirements-dev.txt

install_submodules: ## Installs the required submodules
	git submodule update --init --recursive
	cd ondewo-nlu-client-python && git submodule update --init --recursive

run_code_checks: ## Start the code checks image and run the checks
	docker build -t ${CODE_CHECK_IMAGE} -f dockerfiles/code_checks.Dockerfile .
	docker run --rm ${CODE_CHECK_IMAGE} make flake8
	docker run --rm ${CODE_CHECK_IMAGE} make mypy

install_precommit_hooks: ## Installs pre-commit hooks and sets them up for the ondewo-s2t repo
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg

precommit_hooks_run_all_files: ## Runs all pre-commit hooks on all files and not just the changed ones
	pre-commit run --all-files

clean_pycache:
	rm -rf .pytest_cache
	find . -name '__pycache__' -exec rm -r {} +

run_client_tests: ## Build a little image for running some tests
	docker build -t ${TEST_IMAGE} -f  ondewo-nlu-client-python/dockerfiles/python-test.Dockerfile ./ondewo-nlu-client-python
	docker run --rm ${TEST_IMAGE}

build_ondewo_bpi_example: export image_suffix=$(RELEASE_VERSION)
build_ondewo_bpi_example: ## ondewo-bpi: Builds the ondewo bpi example image
	docker build -t ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:$(image_suffix) -f dockerfiles/ondewo-bpi.Dockerfile .
	docker tag ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:$(image_suffix) ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:latest

push_ondewo_bpi_example: ## ondewo-bpi: Pushes the ondewo bpi example image
	docker push ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:$(image_suffix)
	docker tag ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:$(image_suffix) ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:latest
	docker push ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:latest

build_ondewo_bpi_qa_example: export image_suffix=$(RELEASE_VERSION)
build_ondewo_bpi_qa_example: export image=qa
build_ondewo_bpi_qa_example: build_image_with_tag ## ondewo-bpi-qa: Builds the ondewo bpi qa example image

build_ondewo_bpi_sip_example: export image_suffix=$(RELEASE_VERSION)
build_ondewo_bpi_sip_example: export image=sip
build_ondewo_bpi_sip_example: build_image_with_tag ## ondewo-bpi-sip: Builds the ondewo bpi sip example image

build_image_with_tag:
	docker build -t ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-$(image):$(image_suffix) -f dockerfiles/ondewo-bpi-$(image).Dockerfile .
	docker tag ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-$(image):$(image_suffix) ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-$(image):latest

push_image_with_tag:
	docker push ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-$(image):$(image_suffix)
	docker tag ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-$(image):$(image_suffix) ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-$(image):latest
	docker push ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-$(image):latest

run_ondewo_bpi_example: ## ondewo-bpi: Runs the ondewo bpi example image
	docker compose up ondewo-bpi

kill_ondewo_bpi_example: ## ondewo-bpi: Kills a running ondewo bpi example image
	docker compose kill ondewo-bpi

run_ondewo_bpi_qa_example: ## ondewo-bpi-qa: Runs the ondewo bpi qa example image
	docker compose up ondewo-bpi-qa

kill_ondewo_bpi_qa_example: ## ondewo-bpi-qa: Kills a running ondewo bpi qa example image
	docker compose kill ondewo-bpi-qa


# GRPC autocoder targets
generate_grpc_endpoint_relays: ## Autocode: generate python service files based on protobuf definition of the APIs
	 python -m autocode.generate_endpoint_relays

build_and_push_to_pypi: build_package upload_package clear_package_data  ## Release: build and push to pypi
	echo 'pushed to pypi :)'

build_package: ## Release: build ondewo-bpi package
	python setup.py sdist bdist_wheel

upload_package: ## Release: push to pypi
	twine upload -r pypi dist/*

clear_package_data: ## Release: clear package data directory for a clean build
	rm -rf build dist ondewo_logging.egg-info
