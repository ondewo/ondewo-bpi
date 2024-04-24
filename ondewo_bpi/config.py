# Copyright 2021-2024 ONDEWO GmbH
#
# Licensed under the Apache License, Version 2.0 (the License);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import (
    Optional,
)

from ondewo.logging.decorators import Timer
from ondewo.logging.logger import logger_console as log
from ondewo.nlu.client import Client
from ondewo.nlu.client_config import ClientConfig

import ondewo_bpi.__init__ as file_anchor
from ondewo_bpi.helpers import (
    get_bool_from_env,
    get_int_from_env,
    get_str_from_env,
)

parent = os.path.abspath(os.path.join(os.path.dirname(file_anchor.__file__), os.path.pardir))

# ONDEWO BPI
ONDEWO_BPI_PORT: str = get_str_from_env(env_variable_name="ONDEWO_BPI_PORT", default_value="50051")

# ONDEWO NLU CAI
ONDEWO_BPI_CAI_HOST: Optional[str] = get_str_from_env(
    env_variable_name="ONDEWO_BPI_CAI_HOST",
    default_value="localhost"
)
ONDEWO_BPI_CAI_PORT: Optional[str] = get_str_from_env(env_variable_name="ONDEWO_BPI_CAI_PORT", default_value="50055")
ONDEWO_BPI_CAI_TOKEN: Optional[str] = get_str_from_env(env_variable_name="ONDEWO_BPI_CAI_TOKEN", default_value="")
ONDEWO_BPI_CAI_GRPC_CERT: Optional[str] = get_str_from_env(
    env_variable_name="ONDEWO_BPI_CAI_GRPC_CERT",
    default_value="",
)
ONDEWO_BPI_CAI_HTTP_BASIC_AUTH_TOKEN: Optional[str] = get_str_from_env(
    env_variable_name="ONDEWO_BPI_CAI_HTTP_BASIC_AUTH_TOKEN",
    default_value="",
)
ONDEWO_BPI_CAI_GRPC_SECURE: Optional[bool] = get_bool_from_env(
    env_variable_name="ONDEWO_BPI_CAI_GRPC_SECURE",
    default_value=False
)
ONDEWO_BPI_SENTENCE_TRUNCATION: int = get_int_from_env(
    env_variable_name="ONDEWO_BPI_SENTENCE_TRUNCATION",
    default_value=130,
)
ONDEWO_BPI_CAI_USER_NAME: Optional[str] = get_str_from_env(
    env_variable_name="ONDEWO_BPI_CAI_USER_NAME",
    default_value="",
)
ONDEWO_BPI_CAI_USER_PASS: Optional[str] = get_str_from_env(
    env_variable_name="ONDEWO_BPI_CAI_USER_PASS",
    default_value="",
)

ONDEWO_BPI_CAI_CAI_TOKEN: Optional[str] = get_str_from_env(
    env_variable_name="ONDEWO_BPI_CAI_CAI_TOKEN",
    default_value="",
)


class CentralClientProvider:
    """
    provide a central nlu-client instance to the bpi server without building it on import
    """

    def __init__(self, config: Optional[ClientConfig] = None) -> None:
        self.config = config
        self.client = None
        self._built = False

    @Timer(
        logger=log.debug, log_arguments=False,
        message='CentralClientProvider: get_client: Elapsed time: {}'
    )
    def get_client(self) -> Client:
        if not self._built:
            self._instantiate_client()
            self._built = True
        return self.client

    @Timer(
        logger=log.debug, log_arguments=False,
        message='CentralClientProvider: _instantiate_client: Elapsed time: {}'
    )
    def _instantiate_client(self) -> Client:

        if ONDEWO_BPI_CAI_GRPC_SECURE:
            log.info("configuring secure connection")
            self._instantiate_config(grpc_cert=ONDEWO_BPI_CAI_GRPC_CERT)
            self.client = Client(config=self.config)
        else:
            log.info("configuring INSECURE connection")
            self._instantiate_config()
            self.client = Client(config=self.config, use_secure_channel=False)
        return self.client

    @Timer(
        logger=log.debug, log_arguments=False,
        message='CentralClientProvider: _instantiate_config: Elapsed time: {}'
    )
    def _instantiate_config(self, grpc_cert: Optional[str] = None) -> None:
        if not self.config:
            CentralClientProvider._log_default_config()
            self.config: ClientConfig = ClientConfig(
                host=ONDEWO_BPI_CAI_HOST,
                port=ONDEWO_BPI_CAI_PORT,
                http_token=ONDEWO_BPI_CAI_HTTP_BASIC_AUTH_TOKEN,
                user_name=ONDEWO_BPI_CAI_USER_NAME,
                password=ONDEWO_BPI_CAI_USER_PASS,
                grpc_cert=grpc_cert
            )

    @staticmethod
    @Timer(
        logger=log.debug, log_arguments=False,
        message='CentralClientProvider: _log_default_config: Elapsed time: {}'
    )
    def _log_default_config() -> None:
        client_configuration_str = (
            "\nnlu-client configuration:\n"
            + f"   ONDEWO_BPI_CAI_HOST: '{ONDEWO_BPI_CAI_HOST}'\n"
            + f"   ONDEWO_BPI_CAI_PORT: '{ONDEWO_BPI_CAI_PORT}'\n"
            + f"   ONDEWO_BPI_CAI_GRPC_SECURE: '{ONDEWO_BPI_CAI_GRPC_SECURE}'\n"
            + f"   ONDEWO_BPI_CAI_GRPC_CERT: '{ONDEWO_BPI_CAI_GRPC_CERT}'\n"
            + f"   ONDEWO_BPI_CAI_HTTP_BASIC_AUTH_TOKEN:' {ONDEWO_BPI_CAI_HTTP_BASIC_AUTH_TOKEN}'\n"
            + f"   ONDEWO_BPI_CAI_USER_NAME: '{ONDEWO_BPI_CAI_USER_NAME}'\n"
            + f"   ONDEWO_BPI_CAI_USER_PASS: '{ONDEWO_BPI_CAI_USER_PASS}'\n"
            + f"   ONDEWO_BPI_CAI_CAI_TOKEN: '{ONDEWO_BPI_CAI_CAI_TOKEN}'\n"
        )
        log.info(client_configuration_str)
