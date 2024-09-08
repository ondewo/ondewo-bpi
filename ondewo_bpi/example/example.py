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

from ondewo.logging.decorators import Timer
from ondewo.logging.logger import logger_console as log
from ondewo.nlu import session_pb2
from ondewo.nlu.client import Client

from ondewo_bpi.bpi_server import BpiServer
from ondewo_bpi.config import ONDEWO_BPI_CAI_PORT
from ondewo_bpi.example.login_mock import (
    MockUserLoginServer,
    PortChecker,
)
from ondewo_bpi.intent_max_trigger_handler import IntentMaxTriggerHandler
from ondewo_bpi.message_handler import MessageHandler


class MyServer(BpiServer):
    """
    Example BPI server
    will mock the login to cai to enable start without a cai deployment
    this means if the CAI_PORT (default 50055) is blocked, the example server cannot be started
    """

    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='MyServer: __init__: Elapsed time: {:0.4f}'
    )
    def __init__(self) -> None:
        log.debug("START: Initializing MyServer")
        os.environ["MODULE_NAME"] = "bpi_server"  # update module name for logger
        port_in_use = PortChecker.check_client_users_stub(port=ONDEWO_BPI_CAI_PORT)
        if not port_in_use:
            self.mock_login_server = MockUserLoginServer()
            self.mock_login_server.serve(port=ONDEWO_BPI_CAI_PORT)  # start mock-login server
        super().__init__()  # BpiServer.__init__() triggers Client-init and Login() grpc call
        if not port_in_use:
            self.mock_login_server.kill_server()  # kill mock-login server
        self.register_handlers()
        log.debug("DONE: Initializing MyServer")

    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='MyServer: register_handlers: Elapsed time: {:0.4f}'
    )
    def register_handlers(self) -> None:
        log.debug("START: register_handlers")
        self.register_intent_handler(
            intent_pattern="Default Fallback Intent",
            handlers=[
                self.handle_default_fallback,
            ],
        )
        self.register_intent_handler(
            intent_pattern="Default Exit Intent",
            handlers=[
                self.handle_default_exit,
            ],
        )
        self.register_intent_handler(
            intent_pattern=r"i.my_\.*",
            handlers=[
                self.reformat_text_in_intent,
            ],
        )
        self.register_intent_handler(
            intent_pattern="i.my_handled_intent",
            handlers=[
                self.reformat_text_in_intent,
                IntentMaxTriggerHandler.handle_if_intent_reached_number_triggers_max
            ],
        )
        log.debug("DONE: register_handlers")

    @staticmethod
    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='MyServer: reformat_text_in_intent: Elapsed time: {:0.4f}'
    )
    def reformat_text_in_intent(
        response: session_pb2.DetectIntentResponse,
        nlu_client: Client
    ) -> session_pb2.DetectIntentResponse:
        return MessageHandler.substitute_pattern(
            pattern="<REPLACE:REPLACE_THIS_TEXT>", replace="new text", response=response
        )

    @staticmethod
    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='MyServer: handle_default_fallback: Elapsed time: {:0.4f}'
    )
    def handle_default_fallback(
        response: session_pb2.DetectIntentResponse,
        nlu_client: Client
    ) -> session_pb2.DetectIntentResponse:
        log.info("Default fallback was triggered!")
        return response

    @staticmethod
    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='MyServer: handle_default_exit: Elapsed time: {:0.4f}'
    )
    def handle_default_exit(
        response: session_pb2.DetectIntentResponse,
        nlu_client: Client
    ) -> session_pb2.DetectIntentResponse:
        log.warning("Default exit was triggered!")
        return response

    @staticmethod
    @Timer(
        logger=log.debug,
        log_arguments=False,
        message='MyServer: handle_if_intent_reached_number_triggers_max: Elapsed time: {:0.4f}'
    )
    def handle_if_intent_reached_number_triggers_max(
        response: session_pb2.DetectIntentResponse,
        nlu_client: Client
    ) -> session_pb2.DetectIntentResponse:
        log.warning("Intent was triggered a maximum amount of times!")
        response = IntentMaxTriggerHandler.handle_if_intent_reached_number_triggers_max(response, nlu_client)
        return response

    def serve(self) -> None:
        super().serve()


if __name__ == "__main__":
    server = MyServer()
    server.serve()
