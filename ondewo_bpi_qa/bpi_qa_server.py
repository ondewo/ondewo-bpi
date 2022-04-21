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

import asyncio
import time
from typing import List, Tuple, Coroutine, Any, Dict, Optional

import grpc
from ondewo.logging.decorators import Timer
from ondewo.logging.logger import logger_console
from ondewo.nlu import session_pb2
from ondewo.nlu.context_pb2 import GetContextRequest, Context
from ondewo.nlu.session_pb2 import DetectIntentResponse, DetectIntentRequest, TextInput
from ondewo.qa import qa_pb2, qa_pb2_grpc
from ondewo.qa.qa_pb2 import UrlFilter

from ondewo_bpi.config import SENTENCE_TRUNCATION
from ondewo_bpi_qa.bpi_qa_base_server import BpiQABaseServer
from ondewo_bpi_qa.config import (
    QA_LANG,
    QA_ACTIVE,
    QA_MAX_ANSWERS,
    QA_THRESHOLD_READER,
    QA_THRESHOLD_RETRIEVER,
    QA_HOST,
    QA_PORT,
    SESSION_TIMEOUT_MINUTES,
)
from ondewo_bpi_qa.contants import QA_URL_FILTER_CONTEXT_NAME, QA_URL_FILTER_DEFAULT_PARAM_NAME, \
    QA_URL_FILTER_PROVISIONAL_PARAM_NAME, QA_URL_DEFAULT_FILTER, QA_RESPONSE_NAME, CAI_RESPONSE_NAME


class QAServer(BpiQABaseServer):
    def __init__(self) -> None:
        super().__init__()
        self.qa_client_stub = qa_pb2_grpc.QAStub(channel=grpc.insecure_channel(f"{QA_HOST}:{QA_PORT}"))
        self.loops: Dict[str, Any] = {}  # Async execution loops

    def serve(self) -> None:
        super().serve()

    @Timer(log_arguments=False)
    def DetectIntent(self, request: DetectIntentRequest,
                     context: grpc.ServicerContext) -> DetectIntentResponse:
        self.check_session_id(request)

        if len(request.query_input.text.text) > SENTENCE_TRUNCATION:
            logger_console.info(f'The received text is too long, it will be truncated '
                                f'to {SENTENCE_TRUNCATION} characters!')
        truncated_text: TextInput = TextInput(text=request.query_input.text.text[:SENTENCE_TRUNCATION])
        request.query_input.text.CopyFrom(truncated_text)

        response, response_name = self.handle_predictions(request)

        if response_name == CAI_RESPONSE_NAME:
            # Process CAI response
            response = self.process_messages(response)
            response = self.process_intent_handler(response)
        return response

    def check_session_id(self, request: DetectIntentRequest) -> None:
        session_pop_timeout: int = SESSION_TIMEOUT_MINUTES * 60

        for session in self.loops.copy():
            if time.time() - self.loops[session]["timestamp"] > session_pop_timeout:  # type: ignore
                logger_console.debug(f"Popping old session: {session}.")
                loop = self.loops.pop(session)
                loop["loop"].stop()
                loop["loop"].close()

        if request.session not in self.loops.keys():
            self.loops[request.session] = {
                "loop": asyncio.new_event_loop(),
                "timestamp": time.time(),
            }
            logger_console.debug(
                f"New session in bpi: {request.session}. {len(self.loops)} sessions currently stored."
            )

    @Timer(log_arguments=False)
    def handle_predictions(self, request: DetectIntentRequest, ) -> Tuple[DetectIntentResponse, str]:
        tasks: List[Coroutine] = [self.send_to_cai(request)]
        if QA_ACTIVE:
            tasks.append(self.send_to_qa(request))

        while len(tasks):
            logger_console.debug(f"Starting async loop with {len(tasks)} tasks of type: {type(tasks)}")
            try:
                finished, tasks = self.loops[request.session]["loop"].run_until_complete(
                    asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)  # type: ignore
                )
            except Exception:
                logger_console.exception("Task returned an exception!")
                return DetectIntentResponse(), "exception"

            # Allow the cai_response to return early if it finishes first
            for task in finished:
                result = task.result()
                if result[1] == CAI_RESPONSE_NAME:
                    cai_response = result[0]
                    intent_name_cai = cai_response.query_result.intent.display_name
                    if intent_name_cai != "Default Fallback Intent" or not QA_ACTIVE:
                        logger_console.debug("CAI response good, returning early")
                        return cai_response, CAI_RESPONSE_NAME
                # If the QA response finishes first, save it for later
                else:
                    assert result[1] == QA_RESPONSE_NAME, "Somehow a different response snuck in!"
                    qa_response = result[0]

        qa_confidence = qa_response.query_result.query_result.intent_detection_confidence
        logger_console.debug(f"QA confidence is {qa_confidence}, cutoff is {QA_THRESHOLD_READER}")
        messages = qa_response.query_result.query_result.fulfillment_messages

        if messages:
            return qa_response.query_result, QA_RESPONSE_NAME

        logger_console.debug("No response from QA, passing back Default Fallback.")

        return cai_response, CAI_RESPONSE_NAME

    async def send_to_qa(self, request: DetectIntentRequest, ) -> Tuple[DetectIntentResponse, str]:
        text = request.query_input.text.text
        active_filter: str = QA_URL_DEFAULT_FILTER  # Note: this is a regex inclusion filter

        # Logic to extract a URL filter from the QA_URL_FILTER_CONTEXT_NAME context
        try:
            filter_context: Context = self.client.services.contexts.get_context(
                GetContextRequest(name=f'{request.session}/contexts/{QA_URL_FILTER_CONTEXT_NAME}')
            )
            default_filter: Optional[Context.Parameter] = filter_context.parameters.get(
                QA_URL_FILTER_DEFAULT_PARAM_NAME, None
            )
            provisional_filter: Optional[Context.Parameter] = filter_context.parameters.get(
                QA_URL_FILTER_PROVISIONAL_PARAM_NAME, None
            )
            active_filter = default_filter.value if default_filter else ''

            if provisional_filter:
                active_filter = provisional_filter.value
        except Exception as e:
            logger_console.info(f'No URL filters found')

        qa_request = qa_pb2.GetAnswerRequest(
            session_id=request.session,
            text=session_pb2.TextInput(text=text, language_code=f"{QA_LANG}"),
            max_num_answers=QA_MAX_ANSWERS,
            threshold_reader=QA_THRESHOLD_READER,
            threshold_retriever=QA_THRESHOLD_RETRIEVER,
            url_filter=UrlFilter(regex_filter_include=active_filter)
        )

        logger_console.info(
            {
                "message": f"QA-GetAnswerRequest to QA, text input: {text}",
                "content": text,
                "text": text,
                "tags": ["text"],
                "url filter": active_filter,
            }
        )
        qa_response: DetectIntentResponse = await self.loops[request.session]["loop"].run_in_executor(
            None, self.qa_client_stub.GetAnswer, qa_request,
        )
        # intent_name_qa = qa_response.query_result.intent.display_name
        logger_console.debug({"message": "QA-DetectIntentResponse from QA", "tags": ["text"]})
        return qa_response, QA_RESPONSE_NAME

    async def send_to_cai(self, request: DetectIntentRequest, ) -> Tuple[DetectIntentResponse, str]:
        text = request.query_input.text.text
        logger_console.info(
            {
                "message": f"CAI-DetectIntentRequest to CAI, text input: {text}",
                "content": text,
                "text": text,
                "tags": ["text"],
            }
        )
        cai_response: DetectIntentResponse = await self.loops[request.session]["loop"].run_in_executor(
            None, self.client.services.sessions.detect_intent, request,
        )
        intent_name_cai = cai_response.query_result.intent.display_name
        logger_console.debug(
            {
                "message": f"CAI-DetectIntentResponse from CAI, intent_name_cai: {intent_name_cai}",
                "content": intent_name_cai,
                "intent_name_cai": intent_name_cai,
                "tags": ["text"],
            }
        )
        return cai_response, CAI_RESPONSE_NAME
