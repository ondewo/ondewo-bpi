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

from typing import Dict, List

from ondewo.nlu import intent_pb2, session_pb2
from ondewo.logging.logger import logger_console

import ondewo_bpi.helpers as helpers
from ondewo_bpi.constants import SipTriggers
from ondewo_bpi_sip.bpi_sip_server import SipServer


class MyServer(SipServer):
    def __init__(self) -> None:
        super().__init__()
        self.register_intent_handlers()
        self.register_trigger_handlers()

    def register_intent_handlers(self) -> None:
        self.register_intent_handler(
            intent_name="Default Fallback Intent", handler=self.handle_default_fallback,
        )
        self.register_intent_handler(
            intent_name="Default Exit Intent", handler=self.handle_default_exit,
        )

    def register_trigger_handlers(self) -> None:
        self.register_trigger_handler(
            trigger=SipTriggers.SIP_SEND_NOW.value, handler=self.handle_send_now,
        )
        self.register_trigger_handler(
            trigger=SipTriggers.SIP_HANGUP.value, handler=self.handle_hangup,
        )
        self.register_trigger_handler(
            trigger=SipTriggers.SIP_HUMAN_HANDOVER.value, handler=self.handle_handover,
        )

    @staticmethod
    def handle_default_fallback(response: session_pb2.DetectIntentResponse) -> session_pb2.DetectIntentResponse:
        logger_console.warning("Default fallback was triggered!")
        return response

    @staticmethod
    def handle_default_exit(response: session_pb2.DetectIntentResponse) -> session_pb2.DetectIntentResponse:
        logger_console.warning("Default exit was triggered!")
        return response

    def handle_send_now(
        self,
        response: session_pb2.DetectIntentResponse,
        message: intent_pb2.Intent.Message,
        trigger: str,
        found_triggers: Dict[str, List[str]],
    ) -> None:
        logger_console.warning("injecting text")
        client = self.session_information[helpers.get_session_from_response(response)]["client"]
        for content in found_triggers[trigger]:
            client.services.text_to_speech.send_text_get_filename(
                text_to_send=content, session_id=helpers.get_session_from_response(response)
            )

    def handle_hangup(
        self,
        response: session_pb2.DetectIntentResponse,
        message: intent_pb2.Intent.Message,
        trigger: str,
        found_triggers: Dict[str, List[str]],
    ) -> None:
        logger_console.warning("Hangup Received.")
        client = self.session_information[helpers.get_session_from_response(response)]["client"]
        client.services.voip.hang_up()

    def handle_handover(
        self,
        response: session_pb2.DetectIntentResponse,
        message: intent_pb2.Intent.Message,
        trigger: str,
        found_triggers: Dict[str, List[str]],
    ) -> None:
        logger_console.warning("Handerover Received. Hanging up")
        client = self.session_information[helpers.get_session_from_response(response)]["client"]
        client.services.voip.hang_up()

    def serve(self) -> None:
        super().serve()


if __name__ == "__main__":
    server = MyServer()
    server.serve()
