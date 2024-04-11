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

import threading
import traceback
from concurrent import futures

import grpc
from grpc._channel import _InactiveRpcError
from grpc_reflection.v1alpha import reflection
from ondewo.logging.logger import logger
from ondewo.nlu import (
    user_pb2,
    user_pb2_grpc,
)


class MockUserLoginServer(user_pb2_grpc.UsersServicer):
    """
    'mock' response from Login() endpoint of cai by creating a server and responding
    can be used for testing a bpi-deployment without cai
    yes, this is apparently the simplest way to get a grpc response
    """

    def __init__(self) -> None:
        self.server = None
        self.kill = False
        self.lock = threading.Lock()

    def Login(self, request: user_pb2.LoginRequest, context: grpc.ServicerContext) -> user_pb2.LoginResponse:
        response = user_pb2.LoginResponse(auth_token="mocked", )
        return response

    def setup_reflection(self) -> None:
        service_names = [
            user_pb2.DESCRIPTOR.services_by_name["Users"].full_name,  # type: ignore
        ]

        reflection.enable_server_reflection(service_names=service_names, server=self.server)

    def serve(self, port: str = "50055") -> None:
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        user_pb2_grpc.add_UsersServicer_to_server(self, self.server)
        self.setup_reflection()
        self.server.add_insecure_port(f"[::]:{port}")  # type: ignore

        ## CODE FOR SECURE GRPC REQUEST
        # private_key = open("./ondewo_bpi/example/server.key", 'rb').read()
        # certificate_chain = open("./ondewo_bpi/example/server.crt", 'rb').read()
        # server_credentials = grpc.ssl_server_credentials(
        #     (
        #         (private_key, certificate_chain),
        #     )
        # )
        # self.server.add_secure_port(
        #     address=f"localhost:{port}",
        #     server_credentials=server_credentials
        # )

        logger.info(f"mocking CAI Login @port: {port}")
        self.server.start()  # type: ignore
        logger.info("LoginMock served")

    def kill_server(self) -> None:
        self.kill = True
        self.server.stop(grace=0.4)  # type: ignore
        logger.info("LoginMock killed")


class PortChecker:
    @staticmethod
    def check_client_users_stub(port: str) -> bool:
        """checks if a LoginRequest sent to the given port returns a response (e.g. if cai is reachable)"""
        insecure_channel = grpc.insecure_channel(target=f"localhost:{port}")
        stub = user_pb2_grpc.UsersStub(channel=insecure_channel)
        request = user_pb2.LoginRequest()
        try:
            stub.Login(request=request)
            return True
        except _InactiveRpcError:
            traceback_string = traceback.format_exc()
            if "failed to connect" in traceback_string:
                return False
            elif "Login error. The password provided" in traceback_string:
                return True
        return False
