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
	docker build -t ${TEST_IMAGE} -f  ondewo-nlu-client-python/dockerfiles/ondewo-bpi-pytest.Dockerfile ./ondewo-nlu-client-python
	docker run --rm ${TEST_IMAGE}

build_ondewo_bpi: export image_suffix=$(RELEASE_VERSION)
build_ondewo_bpi: ## ondewo-bpi: Builds the ondewo bpi example image
	docker build -t ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:$(image_suffix) -f dockerfiles/ondewo-bpi.Dockerfile .
	docker tag ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:$(image_suffix) ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:latest

push_ondewo_bpi_example: ## ondewo-bpi: Pushes the ondewo bpi example image
	docker push ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:$(image_suffix)
	docker tag ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:$(image_suffix) ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:latest
	docker push ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi:latest

build_ondewo_bpi_example: export image_suffix=$(RELEASE_VERSION)
build_ondewo_bpi_example: ## ondewo-bpi: Builds the ondewo bpi example image
	docker build -t ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-example:$(image_suffix) -f dockerfiles/ondewo-bpi-example.Dockerfile .
	docker tag ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-example:$(image_suffix) ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-example:latest

push_ondewo_bpi_example: ## ondewo-bpi: Pushes the ondewo bpi example image
	docker push ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-example:$(image_suffix)
	docker tag ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-example:$(image_suffix) ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-example:latest
	docker push ${DOCKER_REGISTRY}/${ONDEWO_NAMESPACE}/ondewo-bpi-example:latest

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

run_ondewo_bpi: ## ondewo-bpi: Runs the ondewo bpi  image
	docker compose up ondewo-bpi ondewo-ingress-envoy

kill_ondewo_bpi: ## ondewo-bpi: Kills a running ondewo bpi  image
	docker compose kill ondewo-bpi ondewo-ingress-envoy

run_ondewo_bpi_example: ## ondewo-bpi-example: Runs the ondewo bpi example image
	docker compose up ondewo-bpi-example ondewo-ingress-envoy

kill_ondewo_bpi_example: ## ondewo-bpi-example: Kills a running ondewo bpi example image
	docker compose kill ondewo-bpi-example ondewo-ingress-envoy

run_ondewo_bpi_qa_example: ## ondewo-bpi-qa: Runs the ondewo bpi qa example image
	docker compose up ondewo-bpi-qa ondewo-ingress-envoy

kill_ondewo_bpi_qa_example: ## ondewo-bpi-qa: Kills a running ondewo bpi qa example image
	docker compose kill ondewo-bpi-qa ondewo-ingress-envoy

# GRPC autocoder targets
generate_grpc_endpoint_relays: ## Autocode: generate python service files based on protobuf definition of the APIs
	python -m autocode.generate_endpoint_relays
	pre-commit run --files ondewo_bpi/autocoded/*

build_and_push_to_pypi: build_package upload_package clear_package_data  ## Release: build and push to pypi
	echo 'pushed to pypi :)'

build_package: ## Release: build ondewo-bpi package
	python setup.py sdist bdist_wheel

upload_package: ## Release: push to pypi
	twine upload -r pypi dist/*

clear_package_data: ## Release: clear package data directory for a clean build
	rm -rf build dist ondewo_logging.egg-info

########################################################
# --- Release                                      --- #
########################################################

ondewo_release: spc create_release_branch create_release_tag ## Release and docker push

create_release_branch: ## Create Release Branch and push it to origin
# check if the branch does not exists and if it exists, delete it
	@if git show-ref --verify --quiet "refs/heads/release/${RELEASE_VERSION}"; then \
        git checkout master; \
		git branch -D "release/${RELEASE_VERSION}"; \
    fi
	git checkout -b "release/${RELEASE_VERSION}"
	git push -u origin "release/${RELEASE_VERSION}"

create_release_tag: ## Create Release Tag and push it to origin
# check if the tag does not exists and if it exists, delete it
	@if git rev-parse -q --verify "refs/tags/$(RELEASE_VERSION)"; then \
        git tag -d $(RELEASE_VERSION); \
		git push origin ":refs/tags/$(RELEASE_VERSION)"; \
    fi
	git tag -a ${RELEASE_VERSION} -m "release/${RELEASE_VERSION}"
	git push origin ${RELEASE_VERSION}

spc: ## Checks if the Release Branch, Tag and Pypi version already exist
	$(eval filtered_branches:= $(shell git branch --all | grep "release/${RELEASE_VERSION}"))
	@if test "$(filtered_branches)" != ""; then \
		echo "-- Test 1: Branch 'release/${RELEASE_VERSION}' exists!!"; \
		read -p "Overwrite the branch? (y/n): " input; \
		if [ "$$input" = "y" ]; then \
			echo "Overwriting Branch 'release/${RELEASE_VERSION}'"; \
		else \
			echo "Branch creation aborted"; \
			exit 1; \
		fi \
	else \
		echo "-- Test 1: Branch 'release/${RELEASE_VERSION}' is free to use"; \
	fi
	$(eval filtered_tags:= $(shell git tag --list | grep "${RELEASE_VERSION}"))
	@if test "$(filtered_tags)" != ""; then \
		echo "-- Test 2: Tag '${RELEASE_VERSION}' exists!!"; \
		read -p "Overwrite the tag? (y/n): " input; \
		if [ "$$input" = "y" ]; then \
			echo "Overwriting tag '${RELEASE_VERSION}'"; \
		else \
			echo "Tag creation aborted!"; \
			exit 1; \
		fi \
	else \
		echo "-- Test 2: Tag '${RELEASE_VERSION}' is free to use"; \
	fi
