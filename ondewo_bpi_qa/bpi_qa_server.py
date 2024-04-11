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

import asyncio
import time
from typing import (
    Any,
    Coroutine,
    Dict,
    List,
    Optional,
    Tuple,
)

import grpc
from ondewo.logging.decorators import Timer
from ondewo.logging.logger import logger_console
from ondewo.nlu import session_pb2
from ondewo.nlu.context_pb2 import (
    Context,
    CreateContextRequest,
    GetContextRequest,
    UpdateContextRequest,
)
from ondewo.nlu.intent_pb2 import Intent
from ondewo.nlu.session_pb2 import (
    CreateSessionRequest,
    DetectIntentRequest,
    DetectIntentResponse,
    GetSessionRequest,
    Session,
    SessionStep,
    TextInput,
    TrackSessionStepRequest,
)
from ondewo.qa import (
    qa_pb2,
    qa_pb2_grpc,
)
from ondewo.qa.qa_pb2 import (
    GetAnswerResponse,
    UrlFilter,
)

from ondewo_bpi.config import SENTENCE_TRUNCATION
from ondewo_bpi_qa.bpi_qa_base_server import BpiQABaseServer
from ondewo_bpi_qa.config import (
    QA_ACTIVE,
    QA_HOST,
    QA_LANG,
    QA_MAX_ANSWERS,
    QA_PORT,
    QA_THRESHOLD_READER,
    QA_THRESHOLD_RETRIEVER,
    SESSION_TIMEOUT_MINUTES,
)
from ondewo_bpi_qa.constants import (
    CAI_RESPONSE_NAME,
    QA_PUBLIC_IMAGE_URI_LINK,
    QA_RESPONSE_NAME,
    QA_URL_DEFAULT_FILTER,
    QA_URL_FILTER_BASE_PARAM_NAME,
    QA_URL_FILTER_CONTEXT_NAME,
    QA_URL_FILTER_PROVISIONAL_PARAM_NAME,
)
from ondewo_bpi_qa.helper import ContextHelper


class QAServer(BpiQABaseServer):
    def __init__(self) -> None:
        super().__init__()
        self.qa_client_stub = qa_pb2_grpc.QAStub(channel=grpc.insecure_channel(f"{QA_HOST}:{QA_PORT}"))
        self.loops: Dict[str, Any] = {}  # Async execution loops

    def serve(self) -> None:
        super().serve()

    @Timer(log_arguments=False, logger=logger_console.debug)
    def DetectIntent(
        self,
        request: DetectIntentRequest,
        context: grpc.ServicerContext
    ) -> DetectIntentResponse:
        self.check_session_id(request)

        if len(request.query_input.text.text) > SENTENCE_TRUNCATION:
            logger_console.info(
                f'The received text is too long, it will be truncated '
                f'to {SENTENCE_TRUNCATION} characters!'
            )
        truncated_text: TextInput = TextInput(text=request.query_input.text.text[:SENTENCE_TRUNCATION])
        request.query_input.text.CopyFrom(truncated_text)

        self.create_session_if_not_exists(request=request)
        request: DetectIntentRequest = self.handle_context_injection_for_qa(request=request)  # Side-effect!
        response, response_name = self.handle_predictions(request=request)

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

    @Timer(log_arguments=False, logger=logger_console.debug)
    def handle_context_injection_for_qa(self, request: DetectIntentRequest, ) -> DetectIntentRequest:
        """
        Note: to enable Q&A to leverage context injection, we made the context injection happen BEFORE
            detect intent is called. This way we can guarantee on our async calls that both Q&A and CAI
            have the same contexts set.

        Note 2: By the nature of it, this function contains a SIDE-EFFECT! It modifies the
            DetectIntentRequest by removing the context "c-qa-url-filter" if found, this context
            is managed manually instead.
        """
        parent: str = ContextHelper.get_agent_path_from_path(request.session)
        unaffected_contexts: List[Context] = []

        if not request.query_params:
            return request

        try:
            qa_url_context: Optional[Context] = self.client.services.contexts.get_context(
                GetContextRequest(name=f'{request.session}/contexts/{QA_URL_FILTER_CONTEXT_NAME}')
            )
        except Exception:
            qa_url_context = None

        for context in request.query_params.contexts:

            if QA_URL_FILTER_CONTEXT_NAME not in context.name:
                unaffected_contexts.append(context)
                continue

            context_to_inject: Context = Context()
            context_to_inject.CopyFrom(context)

            if qa_url_context:
                # Update
                update_context_req: UpdateContextRequest = UpdateContextRequest(context=context_to_inject)
                self.client.services.contexts.update_context(request=update_context_req)
                logger_console.debug(f'Context: {context_to_inject.name} updated!')
            else:
                # Create
                create_context_req: CreateContextRequest = CreateContextRequest(
                    parent=parent,
                    context=context_to_inject
                )
                self.client.services.contexts.create_context(request=create_context_req)
                logger_console.debug(f'Context: {context_to_inject.name} created!')

        del request.query_params.contexts[:]
        request.query_params.contexts.extend(unaffected_contexts)
        return request

    @Timer(log_arguments=False, logger=logger_console.debug)
    def handle_predictions(self, request: DetectIntentRequest, ) -> Tuple[DetectIntentResponse, str]:
        tasks: List[Coroutine] = [self.send_to_cai(request)]
        cai_response: Optional[DetectIntentResponse] = None
        qa_response: Optional[GetAnswerResponse] = None

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
            # track session step if there is a CAI response
            if cai_response:
                qa_response_to_track: GetAnswerResponse = self._fill_in_qa_response_with_cai_response(
                    qa_response=qa_response,
                    cai_response=cai_response
                )
                self.client.services.sessions.track_session_step(
                    TrackSessionStepRequest(
                        session_id=request.session,
                        session_step=SessionStep(
                            detect_intent_request=request,
                            detect_intent_response=qa_response_to_track.query_result,
                            contexts=[],
                        ),
                        session_view=Session.View.VIEW_SPARSE,
                    )
                )
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
            base_filter: Optional[Context.Parameter] = filter_context.parameters.get(
                QA_URL_FILTER_BASE_PARAM_NAME, None
            )
            provisional_filter: Optional[Context.Parameter] = filter_context.parameters.get(
                QA_URL_FILTER_PROVISIONAL_PARAM_NAME, None
            )
            active_filter = base_filter.value if base_filter else active_filter

            if provisional_filter:
                active_filter = provisional_filter.value

        except Exception as e:
            logger_console.info(f'No context: {QA_URL_FILTER_CONTEXT_NAME} found. {e}')
        finally:
            if active_filter == QA_URL_DEFAULT_FILTER:
                logger_console.info('No URL filters found')

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

    def create_session_if_not_exists(self, request: DetectIntentRequest, ) -> None:

        try:
            self.client.services.sessions.get_session(
                request=GetSessionRequest(session_id=request.session, session_view=Session.View.VIEW_SPARSE)
            )
        except Exception:
            logger_console.debug(f'Session {request.session} does not exists.')
            self.client.services.sessions.create_session(
                CreateSessionRequest(
                    parent=ContextHelper.get_agent_path_from_path(request.session),
                    session_uuid=ContextHelper.get_last_uuid_from_path(request.session),
                )
            )
            logger_console.debug(f'Session {request.session} created!')

    # noinspection PyMethodMayBeStatic
    def _fill_in_qa_response_with_cai_response(
        self,
        qa_response: GetAnswerResponse,
        cai_response: DetectIntentResponse
    ) -> GetAnswerResponse:
        """
        This function updates the QA response with information from the CAI response.
        The objective is to create a QA response that can be added to the Session Review History.

            -> Returns a copy of the original qa_response with the modified fields.
        """

        modified_qa_response: GetAnswerResponse = GetAnswerResponse()
        modified_qa_response.CopyFrom(qa_response)

        modified_qa_response.query_result.query_result.action = \
            cai_response.query_result.action
        modified_qa_response.query_result.query_result.parameters.CopyFrom(
            cai_response.query_result.parameters
        )
        modified_qa_response.query_result.query_result.all_required_params_present = \
            cai_response.query_result.all_required_params_present
        modified_qa_response.query_result.query_result.output_contexts.extend(
            cai_response.query_result.output_contexts
        )
        modified_qa_response.query_result.query_result.intent.CopyFrom(
            cai_response.query_result.intent
        )
        modified_qa_response.query_result.query_result.diagnostic_info.CopyFrom(
            cai_response.query_result.diagnostic_info
        )

        current_messages: List[Intent.Message] = list(
            modified_qa_response.query_result.query_result.fulfillment_messages
        )
        del modified_qa_response.query_result.query_result.fulfillment_messages[:]

        for p in Intent.Message.Platform.keys():
            if 'PLACEHOLDER' in p:

                for fm in current_messages:
                    _fm_button: Intent.Message.BasicCard.Button = fm.basic_card.buttons[0]
                    _message: Intent.Message = Intent.Message()
                    _message.is_prompt = False
                    _message.platform = Intent.Message.Platform.Value(p)
                    _message.card.CopyFrom(
                        Intent.Message.Card(
                            title=fm.basic_card.title,
                            subtitle=f'{fm.basic_card.subtitle} - {fm.basic_card.formatted_text}',
                            buttons=[
                                Intent.Message.Card.Button(
                                    text=f'{_fm_button.title}',
                                    postback=f'{_fm_button.open_uri_action.uri}'
                                )
                            ],
                            image_uri=QA_PUBLIC_IMAGE_URI_LINK,
                        )
                    )
                    modified_qa_response.query_result.query_result.fulfillment_messages.append(_message)

        modified_qa_response.query_result.query_result.intent.messages.extend(
            modified_qa_response.query_result.query_result.fulfillment_messages
        )

        return modified_qa_response
