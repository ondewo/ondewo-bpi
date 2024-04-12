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

import time
from concurrent import futures
from typing import (
    List,
    Optional,
)

import grpc
from grpc_reflection.v1alpha import reflection
from ondewo.logging.decorators import Timer
from ondewo.logging.logger import (
    logger,
    logger_console,
    logger_console as log,
)
from ondewo.nlu import (
    agent_pb2,
    agent_pb2_grpc,
    aiservices_pb2,
    aiservices_pb2_grpc,
    ccai_project_pb2,
    ccai_project_pb2_grpc,
    context_pb2,
    context_pb2_grpc,
    entity_type_pb2,
    entity_type_pb2_grpc,
    intent_pb2,
    intent_pb2_grpc,
    operations_pb2,
    operations_pb2_grpc,
    project_role_pb2,
    project_role_pb2_grpc,
    project_statistics_pb2,
    project_statistics_pb2_grpc,
    server_statistics_pb2,
    server_statistics_pb2_grpc,
    session_pb2,
    session_pb2_grpc,
    user_pb2,
    user_pb2_grpc,
    utility_pb2,
    utility_pb2_grpc,
)
from ondewo.nlu.client import Client as NLUClient
from ondewo.qa import qa_pb2_grpc

from ondewo_bpi.bpi_services import (
    BpiAgentsServices,
    BpiAiServicesServices,
    BpiCcaiProjectsServices,
    BpiContextServices,
    BpiEntityTypeServices,
    BpiIntentsServices,
    BpiOperationsServices,
    BpiProjectRolesServices,
    BpiProjectStatisticsServices,
    BpiServerStatisticsServices,
    BpiSessionsServices,
    BpiUsersServices,
    BpiUtilitiesServices,
)
from ondewo_bpi.config import (
    CentralClientProvider,
    PORT,
)


class BpiServer(
    BpiAgentsServices,
    BpiAiServicesServices,
    BpiCcaiProjectsServices,
    BpiContextServices,
    BpiEntityTypeServices,
    BpiIntentsServices,
    BpiProjectRolesServices,
    BpiSessionsServices,
    BpiUsersServices,
    BpiProjectStatisticsServices,
    BpiOperationsServices,
    BpiServerStatisticsServices,
    BpiUtilitiesServices,
):
    @property
    def client(self) -> NLUClient:
        return self._client

    @client.setter
    def client(self, value: NLUClient) -> None:
        self._client = value

    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='BpiServer: __init__: Elapsed time: {}'
    )
    def __init__(self, client_provider: Optional[CentralClientProvider] = None) -> None:
        super().__init__()
        if not client_provider:
            self.client = CentralClientProvider().get_client()
        else:
            self.client = client_provider.get_client()
        self.server = None
        self.services_descriptors: List[str] = [
            agent_pb2.DESCRIPTOR.services_by_name['Agents'].full_name,
            aiservices_pb2.DESCRIPTOR.services_by_name['AiServices'].full_name,
            ccai_project_pb2.DESCRIPTOR.services_by_name['CcaiProjects'].full_name,
            context_pb2.DESCRIPTOR.services_by_name['Contexts'].full_name,
            entity_type_pb2.DESCRIPTOR.services_by_name['EntityTypes'].full_name,
            intent_pb2.DESCRIPTOR.services_by_name['Intents'].full_name,
            operations_pb2.DESCRIPTOR.services_by_name['Operations'].full_name,
            project_role_pb2.DESCRIPTOR.services_by_name['ProjectRoles'].full_name,
            project_statistics_pb2.DESCRIPTOR.services_by_name['ProjectStatistics'].full_name,
            server_statistics_pb2.DESCRIPTOR.services_by_name['ServerStatistics'].full_name,
            session_pb2.DESCRIPTOR.services_by_name['Sessions'].full_name,
            user_pb2.DESCRIPTOR.services_by_name['Users'].full_name,
            utility_pb2.DESCRIPTOR.services_by_name['Utilities'].full_name,
        ]

    def _setup_reflection(self) -> None:
        reflection.enable_server_reflection(service_names=self.services_descriptors, server=self.server)

    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='BpiServer: _add_services: Elapsed time: {}'
    )
    def _add_services(self) -> None:
        agent_pb2_grpc.add_AgentsServicer_to_server(self, self.server)
        aiservices_pb2_grpc.add_AiServicesServicer_to_server(self, self.server)
        ccai_project_pb2_grpc.add_CcaiProjectsServicer_to_server(self, self.server)
        context_pb2_grpc.add_ContextsServicer_to_server(self, self.server)
        entity_type_pb2_grpc.add_EntityTypesServicer_to_server(self, self.server)
        intent_pb2_grpc.add_IntentsServicer_to_server(self, self.server)
        operations_pb2_grpc.add_OperationsServicer_to_server(self, self.server)
        project_role_pb2_grpc.add_ProjectRolesServicer_to_server(self, self.server)
        project_statistics_pb2_grpc.add_ProjectStatisticsServicer_to_server(self, self.server)
        server_statistics_pb2_grpc.add_ServerStatisticsServicer_to_server(self, self.server)
        session_pb2_grpc.add_SessionsServicer_to_server(self, self.server)
        user_pb2_grpc.add_UsersServicer_to_server(self, self.server)
        utility_pb2_grpc.add_UtilitiesServicer_to_server(self, self.server)

    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='BpiServer: _setup_server: Elapsed time: {}'
    )
    def _setup_server(self) -> None:
        logger.info("attempting to setup server...")
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self._add_services()
        self._setup_reflection()
        self.server.add_insecure_port(f"[::]:{PORT}")  # type: ignore
        # self.server.add_insecure_port(f"0.0.0.0:{PORT}")  # type: ignore
        logger.info(f"SERVING SERVER AT SERVING PORT {PORT}")
        self.server.start()  # type: ignore

    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='BpiServer: serve: Elapsed time: {}'
    )
    def serve(self) -> None:
        logger_console.info(f"attempting to start server on port {PORT}")
        self._setup_server()
        logger_console.info({"message": f"Server started on port {PORT}", "content": PORT})
        logger_console.info(
            {
                "message": f"using intent handlers list: {self.intent_handlers}",
                "content": self.intent_handlers,
            }
        )
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger_console.info("Keyboard interrupt, shutting down")
        logger_console.info({"message": "server shut down", "tags": ["timing"]})


if __name__ == "__main__":
    server = BpiServer()
    server.serve()
