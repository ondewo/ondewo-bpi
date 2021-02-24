# Copyright 2021 ONDEWO GmbH
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

from ondewo.nlu.client import Client as NLUClient
from ondewo.qa import qa_pb2, qa_pb2_grpc
from ondewo.qa.client import Client as QAClient

from ondewo_bpi.bpi_server import BpiServer
from ondewo_bpi_qa.bpi_qa_services import BpiQAServices
from ondewo_bpi_qa.config import QAClientProvider


class BpiQABaseServer(
    BpiServer,
    BpiQAServices,
):
    @property
    def client(self) -> NLUClient:
        return self._client

    @client.setter
    def client(self, value: NLUClient) -> None:
        self._client = value

    @property
    def qa_client(self) -> QAClient:
        return self._qa_client

    @qa_client.setter
    def qa_client(self, value: QAClient) -> None:
        self._qa_client = value

    def __init__(self) -> None:
        super(BpiQABaseServer, self).__init__()
        self.qa_client = QAClientProvider().get_client()
        self.services_descriptors.append(qa_pb2.DESCRIPTOR.services_by_name["QA"].full_name)  # type: ignore

    def _add_services(self) -> None:
        super(BpiQABaseServer, self)._add_services()
        qa_pb2_grpc.add_QAServicer_to_server(self, self.server)
