from typing import Tuple

from docker.models.containers import Container
from sip.utils.custom_docker_comm import CustomDockerClient


class TestBpiServer:
    def test_if_container_starts(
        self, bpi_server: Tuple[Container, CustomDockerClient],
    ):
        container, custom_docker_client = bpi_server
        health = custom_docker_client.check_health(container_id=container.id)
        assert health
