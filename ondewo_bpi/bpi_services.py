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
from abc import (
    ABCMeta,
    abstractmethod,
)
from concurrent.futures import ThreadPoolExecutor
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
)

import grpc
import regex as re
from google.protobuf.json_format import MessageToJson
from ondewo.logging.decorators import Timer
from ondewo.logging.logger import logger_console as log
from ondewo.nlu import (
    context_pb2,
    intent_pb2,
    session_pb2,
    user_pb2,
)
from ondewo.nlu.client import Client as NluClient
from ondewo.nlu.session_pb2 import TextInput

from ondewo_bpi.autocoded.agent_grpc_autocode import AutoAgentsServicer
from ondewo_bpi.autocoded.aiservices_grpc_autocode import AutoAiServicesServicer
from ondewo_bpi.autocoded.ccai_project_grpc_autocode import AutoCcaiProjectsServicer
from ondewo_bpi.autocoded.context_grpc_autocode import AutoContextsServicer
from ondewo_bpi.autocoded.entity_type_grpc_autocode import AutoEntityTypesServicer
from ondewo_bpi.autocoded.intent_grpc_autocode import AutoIntentsServicer
from ondewo_bpi.autocoded.operations_grpc_autocode import AutoOperationsServicer
from ondewo_bpi.autocoded.project_role_grpc_autocode import AutoProjectRolesServicer
from ondewo_bpi.autocoded.project_statistics_grpc_autocode import AutoProjectStatisticsServicer
from ondewo_bpi.autocoded.server_statistics_grpc_autocode import AutoServerStatisticsServicer
from ondewo_bpi.autocoded.session_grpc_autocode import AutoSessionsServicer
from ondewo_bpi.autocoded.user_grpc_autocode import AutoUsersServicer
from ondewo_bpi.autocoded.utility_grpc_autocode import AutoUtilitiesServicer
from ondewo_bpi.config import ONDEWO_BPI_SENTENCE_TRUNCATION
from ondewo_bpi.constants import (
    QueryTriggers,
    SipTriggers,
)
from ondewo_bpi.helpers import (
    clear_created_modified,
    get_session_from_response,
)
from ondewo_bpi.message_handler import (
    MessageHandler,
)


@dataclass()
class IntentCallbackAssignor:
    """Class for keeping track of the intents and their handlers"""
    sort_index: int = field(init=False, repr=False)
    intent_pattern: str
    handlers: List[Callable]

    def __gt__(self, other: 'IntentCallbackAssignor') -> bool:
        return self.sort_index > other.sort_index

    def __lt__(self, other: 'IntentCallbackAssignor') -> bool:
        return self.sort_index < other.sort_index

    def __post_init__(self):
        object.__setattr__(self, 'sort_index', len(self.intent_pattern))


class BpiSessionsServices(AutoSessionsServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass

    @Timer(
        logger=log.debug, log_arguments=False,
        message='BpiSessionsServices: __init__: Elapsed time: {}'
    )
    def __init__(self) -> None:
        self.intent_handlers: List[IntentCallbackAssignor] = list()
        self.trigger_handlers: Dict[str, Callable] = {
            i.value: self.trigger_function_not_implemented for i in [*SipTriggers, *QueryTriggers]
        }

    @Timer(
        logger=log.debug, log_arguments=True,
        message='BpiSessionsServices: register_intent_handler: Elapsed time: {}'
    )
    def register_intent_handler(self, intent_pattern: str, handlers: List[Callable]) -> None:
        intent_handler: IntentCallbackAssignor = IntentCallbackAssignor(
            intent_pattern=intent_pattern,
            handlers=handlers,
        )
        self.intent_handlers.append(intent_handler)
        self.intent_handlers = sorted(self.intent_handlers, reverse=True)

    @Timer(
        logger=log.debug, log_arguments=False,
        message='BpiSessionsServices: register_trigger_handler: Elapsed time: {}'
    )
    def register_trigger_handler(self, trigger: str, handler: Callable) -> None:
        self.trigger_handlers[trigger] = handler

    @Timer(
        logger=log.debug, log_arguments=True,
        message='BpiSessionsServices: trigger_function_not_implemented: Elapsed time: {}'
    )
    def trigger_function_not_implemented(
        self,
        response: session_pb2.DetectIntentResponse,
        message: intent_pb2.Intent.Message,
        trigger: str,
        found_triggers: Dict[str, List[str]],
    ) -> None:
        log.warning(
            {
                "message": f"no function for the trigger {trigger}, please subclass and implement",
                "trigger": trigger,
                "content": found_triggers[trigger],
            }
        )

    @Timer(
        logger=log.debug, log_arguments=True,
        message='BpiSessionsServices: DetectIntent: Elapsed time: {}'
    )
    def DetectIntent(
        self,
        request: session_pb2.DetectIntentRequest,
        context: grpc.ServicerContext,
    ) -> session_pb2.DetectIntentResponse:
        try:
            if len(request.query_input.text.text) > ONDEWO_BPI_SENTENCE_TRUNCATION:
                log.warning(
                    f'The received text is too long, it will be truncated '
                    f'to {ONDEWO_BPI_SENTENCE_TRUNCATION} characters!'
                )
            log.debug(f'BpiSessionsServices: DetectIntent: request: \n{request}')
            truncated_text: TextInput = TextInput(text=request.query_input.text.text[:ONDEWO_BPI_SENTENCE_TRUNCATION])
            truncated_text.language_code = request.query_input.text.language_code
            log.debug(f'BpiSessionsServices: DetectIntent: truncated_text: \n{truncated_text}')
            request.query_input.text.CopyFrom(truncated_text)
            text = request.query_input.text.text
        except Exception as e:
            log.exception(
                f"An issue was encountered in BPI:\n"
                f"\tSeems like the request query_input data was not properly formatted\n"
                f"\tDetails: {e}"
            )
            text = "error"
        log.debug(
            {
                "message": f"CAI-DetectIntentRequest to CAI, text input: {text}",
                "content": text,
                "text": text,
                "tags": ["text"],
            }
        )
        cai_response: session_pb2.DetectIntentResponse = self.perform_detect_intent(request)
        output_contexts_cai_response_dict: Dict[str, Tuple[str, context_pb2.Context]] = {
            output_context.name: (MessageToJson(message=output_context, sort_keys=True, indent=True), output_context)
            for output_context in cai_response.query_result.output_contexts
        }
        intent_name: str = cai_response.query_result.intent.display_name
        log.debug(
            {
                "message": f"CAI-DetectIntentResponse from CAI, intent_name: {intent_name}",
                "content": intent_name,
                "intent_name": intent_name,
                "session_id": get_session_from_response(cai_response),
                "tags": ["text"],
            }
        )
        cai_response = self.process_messages(cai_response)
        processed_cai_response: session_pb2.DetectIntentResponse = self.process_intent_handler(cai_response)

        output_contexts_cai_response_processed_dict: Dict[str, Tuple[str, context_pb2.Context]] = {
            output_context.name: (MessageToJson(message=output_context, sort_keys=True, indent=True), output_context)
            for output_context in cai_response.query_result.output_contexts
        }
        # region single thread context update
        # for context_name in output_contexts_cai_response_dict.keys():
        #     context_str: str = output_contexts_cai_response_dict[context_name][0]
        #     context_processed_str = output_contexts_cai_response_processed_dict[context_name][0]
        #     if context_str != context_processed_str:
        #         # Update the modified context from bpi in cai
        #         context_to_update: context_pb2.Context = output_contexts_cai_response_dict[context_name][1]
        #         clear_created_modified(context_to_update)
        #         update_context_request: context_pb2.UpdateContextRequest = context_pb2.UpdateContextRequest(
        #             context=context_to_update,
        #         )
        #         self.client.services.contexts.update_context(update_context_request)
        # endregion single thread context update
        # region multi thread context update
        BpiSessionsServices.process_in_threadpool(
            output_contexts_cai_response_dict=output_contexts_cai_response_dict,
            output_contexts_cai_response_processed_dict=output_contexts_cai_response_processed_dict,
            client=self.client,
        )
        # endregion multi thread context update

        # TODO(arath): add here to update the modified response in ondewo-cai session step once API is ready
        return processed_cai_response

    @staticmethod
    def process_context(
        context_name: str,
        output_contexts_cai_response_dict: Dict[str, Tuple[str, context_pb2.Context]],
        output_contexts_cai_response_processed_dict: Dict[str, Tuple[str, context_pb2.Context]],
        client: NluClient,
    ) -> None:
        # Update the modified context from bpi in cai
        context_to_update: context_pb2.Context = output_contexts_cai_response_dict[context_name][1]
        if context_to_update.lifespan_count > 0:
            clear_created_modified(context_to_update)
            update_context_request: context_pb2.UpdateContextRequest = context_pb2.UpdateContextRequest(
                context=context_to_update,
            )
            log.debug(f"START: Send process_context for context {context_name} ...")
            client.services.contexts.update_context(update_context_request)
            log.debug(f"DONE: Send process_context for context {context_name}.")

    @staticmethod
    def process_in_threadpool(
        output_contexts_cai_response_dict: Dict[str, Tuple[str, context_pb2.Context]],
        output_contexts_cai_response_processed_dict: Dict[str, Tuple[str, context_pb2.Context]],
        client: NluClient,
    ) -> None:
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit tasks to the thread pool
            for context_name in output_contexts_cai_response_dict.keys():
                if context_name in output_contexts_cai_response_processed_dict:
                    context_str: str = output_contexts_cai_response_dict[context_name][0]
                    context_processed_str: str = output_contexts_cai_response_processed_dict[context_name][0]
                    if context_str == context_processed_str:
                        # do not update context if context has not changed through ondewo-bpi processing
                        continue

                executor.submit(
                    BpiSessionsServices.process_context,
                    context_name=context_name,
                    output_contexts_cai_response_dict=output_contexts_cai_response_dict,
                    output_contexts_cai_response_processed_dict=output_contexts_cai_response_processed_dict,
                    client=client,
                )

    @Timer(
        logger=log.debug, log_arguments=True, recursive=True,
        message='BpiSessionsServices: perform_detect_intent: Elapsed time: {}'
    )
    def perform_detect_intent(
        self,
        request: session_pb2.DetectIntentRequest,
    ) -> session_pb2.DetectIntentResponse:
        log.debug(f'START: BpiSessionsServices: perform_detect_intent: request: \n{request}')
        response: session_pb2.DetectIntentResponse = self.client.services.sessions.detect_intent(request)
        log.debug(f'DONE: BpiSessionsServices: perform_detect_intent: response: \n{response}')
        return response

    @Timer(
        logger=log.debug, log_arguments=True, recursive=True,
        message='BpiSessionsServices: process_messages: Elapsed time: {}'
    )
    def process_messages(
        self,
        response: session_pb2.DetectIntentResponse,
    ) -> session_pb2.DetectIntentResponse:
        for j, message in enumerate(response.query_result.fulfillment_messages):
            found_triggers = MessageHandler.get_triggers(message, get_session_from_response(response))

            for found_trigger in found_triggers:
                new_response: Optional[session_pb2.DetectIntentResponse] = \
                    self.trigger_handlers[found_trigger](response, message, found_trigger, found_triggers)

                if new_response:
                    if not new_response.response_id == response.response_id:
                        return new_response

            # FIXME: add if needed to remove special trigger commands from text in message:
            # for found_trigger in found_triggers:
            #     log.debug(f'BpiSessionsServices: process_messages: found_trigger: {found_trigger}')
            #     SingleMessageHandler.substitute_pattern_in_message(message, found_trigger, "")
            #     log.debug(f'BpiSessionsServices: process_messages: found_trigger: {found_trigger}')

            self.quicksend_to_api(response, message, j)
        if not len(response.query_result.fulfillment_messages):
            self.quicksend_to_api(response, None, 0)

        return response

    @Timer(
        logger=log.debug, log_arguments=False,
        message='BpiSessionsServices: quicksend_to_api: Elapsed time: {}'
    )
    def quicksend_to_api(
        self,
        response: session_pb2.DetectIntentResponse,
        message: Optional[intent_pb2.Intent.Message],
        count: int,
    ) -> None:
        log.warning({"message": "quicksend_to_api not written, please subclass and implement"})

    @Timer(
        logger=log.debug, log_arguments=True, recursive=True,
        message='BpiSessionsServices: process_intent_handler: Elapsed time: {}'
    )
    def process_intent_handler(
        self,
        cai_response: session_pb2.DetectIntentResponse,
    ) -> session_pb2.DetectIntentResponse:
        # Create an ordered dictionary by key value length
        intent_name = cai_response.query_result.intent.display_name
        handlers: List[Callable] = self._get_handlers_for_intent(
            intent_name=intent_name,
            assignors=self.intent_handlers,
        )
        for handler in handlers:
            cai_response = handler(cai_response, self.client)
            text = [i.text.text for i in cai_response.query_result.fulfillment_messages]
            log.info(
                {
                    "message": f"BPI-DetectIntentResponse from BPI with text: {text}",
                    "content": text,
                    "text": text,
                    "tags": ["text", "clean"],
                }
            )
        return cai_response

    @Timer(
        logger=log.debug, log_arguments=False,
        message='BpiSessionsServices: _get_handlers_for_intent: Elapsed time: {}'
    )
    def _get_handlers_for_intent(
        self,
        intent_name: str,
        assignors: List[IntentCallbackAssignor],
    ) -> List[Callable]:
        for assignor in assignors:
            # NOTE: the intent names are regex patterns. For exact intent match, prefix with ^ and postfix with $
            if re.match(assignor.intent_pattern, intent_name):
                return assignor.handlers
        return []


class BpiUsersServices(AutoUsersServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass

    def Login(self, request: user_pb2.LoginRequest, context: grpc.ServicerContext) -> user_pb2.LoginResponse:
        log.info(f'Login request handled by bpi\n Login user: {request.user_email}')
        return super().Login(request, context)


class BpiContextServices(AutoContextsServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass

    def CreateContext(
        self, request: context_pb2.CreateContextRequest, context: grpc.ServicerContext
    ) -> context_pb2.Context:
        log.info("passing create context request on to CAI")
        return self.client.services.contexts.create_context(request=request)


class BpiAgentsServices(AutoAgentsServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiEntityTypeServices(AutoEntityTypesServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiAiServicesServices(AutoAiServicesServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiIntentsServices(AutoIntentsServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiProjectRolesServices(AutoProjectRolesServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiCcaiProjectsServices(AutoCcaiProjectsServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiProjectStatisticsServices(AutoProjectStatisticsServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiServerStatisticsServices(AutoServerStatisticsServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiOperationsServices(AutoOperationsServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass


class BpiUtilitiesServices(AutoUtilitiesServicer):
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> NluClient:
        pass
