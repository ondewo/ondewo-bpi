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

from dotenv import load_dotenv
from ondewo.logging.logger import (
    logger,
    logger_console,
)
from ondewo.nlu.client import Client
from ondewo.nlu.client_config import ClientConfig

import ondewo_bpi.__init__ as file_anchor
from ondewo_bpi.helpers import get_bool_from_env

parent = os.path.abspath(os.path.join(os.path.dirname(file_anchor.__file__), os.path.pardir))

# load default configuration from the environment
load_dotenv("./bpi.env")

# ONDEWO BPI
PORT: str = os.getenv("PORT", "50051")

# ONDEWO NLU CAI
CAI_HOST: Optional[str] = os.getenv("CAI_HOST", "localhost")
CAI_PORT: Optional[str] = os.getenv("CAI_PORT", "50055")
CAI_TOKEN: Optional[str] = os.getenv("CAI_TOKEN")
GRPC_CERT: Optional[str] = os.getenv("GRPC_CERT")
HTTP_BASIC_AUTH_TOKEN: Optional[str] = os.getenv("HTTP_BASIC_AUTH_TOKEN")
GRPC_SECURE: Optional[bool] = get_bool_from_env(env_variable_name="GRPC_SECURE", default_value="False")
SENTENCE_TRUNCATION: int = int(os.getenv("SENTENCE_TRUNCATION", '130'))
USER_NAME: Optional[str] = os.getenv("USER_NAME")
USER_PASS: Optional[str] = os.getenv("USER_PASS")


class CentralClientProvider:
    """
    provide a central nlu-client instance to the bpi server without building it on import
    """

    def __init__(self, config: Optional[ClientConfig] = None) -> None:
        self.config = config
        self.client = None
        self._built = False

    def get_client(self) -> Client:
        if not self._built:
            self._instantiate_client()
            self._built = True
        return self.client

    def _instantiate_client(self) -> Client:

        if GRPC_SECURE:
            logger.info("configuring secure connection")
            self._instantiate_config(grpc_cert=GRPC_CERT)
            self.client = Client(config=self.config)
        else:
            logger.info("configuring INGRPC_SECURE connection")
            self._instantiate_config()
            self.client = Client(config=self.config, use_secure_channel=False)
        return self.client

    def _instantiate_config(self, grpc_cert: Optional[str] = None) -> None:
        if not self.config:
            self._log_default_config()
            self.config: ClientConfig = ClientConfig(
                host=CAI_HOST,
                port=CAI_PORT,
                http_token=HTTP_BASIC_AUTH_TOKEN,
                user_name=USER_NAME,
                password=USER_PASS,
                grpc_cert=grpc_cert
            )

    def _log_default_config(self) -> None:
        client_configuration_str = (
            "\nnlu-client configuration:\n"
            + f"   Secure: {GRPC_SECURE}\n"
            + f"   Host: {CAI_HOST}\n"
            + f"   Port: {CAI_PORT}\n"
            + f"   Http_token: {HTTP_BASIC_AUTH_TOKEN}\n"
            + f"   User_name: {USER_NAME}\n"
            + f"   Password: {USER_PASS}\n"
        )
        logger_console.info(client_configuration_str)
