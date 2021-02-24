import time
from typing import Generator

import pytest
from sip.utils.custom_docker_comm import CustomDockerClient


@pytest.fixture(scope="function")
def bpi_example_server() -> Generator:
    custom_docker_client = CustomDockerClient()
    compose_file = "docker-compose.yaml"
    env_file = None

    # stop container if running
    container_name = "bpi"
    custom_docker_client.compose.down(
        compose_file=compose_file, environment_file=env_file, service_name=container_name,
    )
    custom_docker_client.remove_container_if_there(container_name=container_name)
    time.sleep(0.5)

    # start example server
    custom_docker_client.compose.up(
        compose_file=compose_file, environment_file=env_file, service_name=container_name,
    )
    active_containers = custom_docker_client.get_running_container_names()
    for container_name in active_containers:
        if "bpi" in container_name:
            break
    container = custom_docker_client.get_container_objects(services=[container_name])[0]
    time.sleep(1.0)

    yield container, custom_docker_client

    custom_docker_client.compose.down(
        compose_file=compose_file, environment_file=env_file,
    )
    container.stop()
