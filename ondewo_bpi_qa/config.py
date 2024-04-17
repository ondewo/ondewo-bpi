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
    Tuple,
)

from ondewo.logging.logger import logger_console as log
from ondewo.qa.client import Client
from ondewo.qa.client_config import ClientConfig

QA_HOST: str = os.getenv("QA_HOST", "172.17.0.1")
QA_PORT: str = os.getenv("QA_PORT", "50052")
QA_LANG: str = os.getenv("QA_LANG", "de")

SESSION_TIMEOUT_MINUTES: int = 20

QA_MAX_ANSWERS: int = int(os.getenv("QA_MAX_ANSWERS", "3"))
QA_THRESHOLD_READER: float = float(os.getenv("QA_THRESHOLD_READER", "0.5"))
QA_THRESHOLD_RETRIEVER: float = float(os.getenv("QA_THRESHOLD_RETRIEVER", "0.5"))
QA_ACTIVE: bool = True if os.getenv("QA_ACTIVE", "False") == "True" else False
QA_GRPC_SECURE: Optional[str] = os.getenv("QA_GRPC_SECURE", "False")

client_configuration_str = (
    "\nqa-client configuration:\n"
    + f"   Secure: {QA_GRPC_SECURE}\n"
    + f"   Host: {QA_HOST}\n"
    + f"   Port: {QA_PORT}\n"
    + f"   Language: {QA_LANG}\n"
    + f"   Number of answers per query: {QA_MAX_ANSWERS}\n"
    + f"   Reader threshold: {QA_THRESHOLD_READER}\n"
    + f"   Retriever threshold: {QA_THRESHOLD_RETRIEVER}\n"
    + f"   Is active?: {QA_ACTIVE}\n"
)
log.info(client_configuration_str)


class QAClientProvider:
    """
    provide a central qa-client instance to the bpi server without building it on import
    """

    def __init__(self) -> None:
        self.config = None
        self.client = None
        self._built = False

    def instantiate_client(self, qa_port: str = "") -> Tuple[ClientConfig, Client]:
        if qa_port == "":
            qa_port = QA_PORT

        if QA_GRPC_SECURE:
            log.warning("Secure connection not possible for Question&Answering.")
            log.warning("Using insecure connection instead...")

        log.info("configuring INSECURE connection")
        self.config = ClientConfig(host=QA_HOST, port=qa_port, )
        self.client = Client(config=self.config, use_secure_channel=False)
        return self.config, self.client

    def get_client(self, qa_port: str = "") -> Client:
        if not self._built:
            self.config, self.client = self.instantiate_client(qa_port=qa_port)
            self._built = True

        return self.client
