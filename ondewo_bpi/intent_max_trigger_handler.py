from collections import Counter
from typing import (
    Dict,
    List,
    Optional,
)

from google.protobuf.json_format import MessageToDict
from ondewo.nlu import context_pb2
from ondewo.nlu.client import Client
from ondewo.nlu.session_pb2 import (
    DetectIntentRequest,
    DetectIntentResponse,
    GetSessionRequest,
    QueryInput,
    QueryParameters,
    Session,
    TextInput,
)


class IntentMaxTriggerHandler:
    intent_with_max_number_triggers_dict = {'Default Fallback Intent': 2, 'Default Exit Intent': 2}

    @classmethod
    def _get_session(cls, nlu_client: Client, session_id: str) -> Session:
        get_session_request: GetSessionRequest = GetSessionRequest(
            session_id=session_id,
            session_view=Session.View.VIEW_SPARSE
        )
        nlu_session: Session = nlu_client.services.sessions.get_session(request=get_session_request)
        return nlu_session

    @classmethod
    def _get_matched_intents(cls, nlu_client: Client, session_id: str) -> List[Dict]:
        session_dict: Dict = MessageToDict(cls._get_session(nlu_client, session_id))
        matched_intents: List[Dict] = session_dict['sessionInfo']['matchedIntents']
        return matched_intents

    @classmethod
    def _get_intent_display_name_list(cls, nlu_client: Client, session_id: str) -> List[str]:
        matched_intents: List[Dict] = cls._get_matched_intents(nlu_client, session_id)
        intent_display_name_list: List[str] = []
        for matched_intent in matched_intents:
            intent_display_name_list.append(matched_intent['displayName'])
        return intent_display_name_list

    @classmethod
    def _get_intent_display_name_counter(cls, nlu_client: Client, session_id: str) -> Counter:
        intent_display_name_list: List[str] = cls._get_intent_display_name_list(nlu_client, session_id)
        return Counter(intent_display_name_list)

    @classmethod
    def _check_if_intent_reached_number_triggers_max(cls, intent_name: str, nlu_client: Client, session_id: str):
        max_number_triggers_for_intent: Optional[int] = cls.intent_with_max_number_triggers_dict.get(intent_name)
        if max_number_triggers_for_intent:
            intent_display_name_counter: Counter = cls._get_intent_display_name_counter(nlu_client, session_id)
            current_number_triggers: Optional[int] = intent_display_name_counter.get(intent_name)
            if current_number_triggers and current_number_triggers >= max_number_triggers_for_intent:
                return True
        return False

    @classmethod
    def _get_default_exit_detect_intent_request(cls, session_id: str, language_code: str) -> DetectIntentRequest:
        context: context_pb2.Context = cls._create_context_for_triggering_default_exit_intent(session_id)

        nlu_request: DetectIntentRequest = DetectIntentRequest(
            session=session_id,
            query_input=QueryInput(
                text=TextInput(
                    text="Default Exit Intent",
                    language_code=language_code,
                )
            ),
            query_params=QueryParameters(
                contexts=[context]
            )
        )
        return nlu_request

    @classmethod
    def _create_context_for_triggering_default_exit_intent(cls, session_id: str) -> context_pb2.Context:
        # Enter intent name .. Example would be i.order.pizza
        intent_name: str = "Default Exit Intent"
        context_parameter: context_pb2.Context.Parameter = context_pb2.Context.Parameter(
            display_name='intent_name',
            value=intent_name
        )

        # intent_name in display_name and parameter "dictionary" are hardcoded. So don't change them
        parameter: Dict[str, context_pb2.Context.Parameter] = {'intent_name': context_parameter}

        # Don't change the name, just change the lifespan_count,
        #   which defines how many times this context is going to be injected.
        context = context_pb2.Context(
            name=f"{session_id}/contexts/exact_intent",
            lifespan_count=1,  # Note: the intent will be set only for the next interaction and then decay
            parameters=parameter
        )

        return context

    @classmethod
    def handle_if_intent_reached_number_triggers_max(
        cls,
        nlu_response: DetectIntentResponse,
        nlu_client: Client,
    ) -> DetectIntentResponse:
        nlu_response_dict: Dict = MessageToDict(nlu_response)
        intent_name: str = nlu_response_dict['queryResult']['intent']['displayName']
        language_code: str = nlu_response_dict['queryResult']["languageCode"]
        session_id: str = nlu_response_dict['queryResult']['diagnosticInfo']['sessionId']

        if cls._check_if_intent_reached_number_triggers_max(intent_name, nlu_client, session_id):
            nlu_request: DetectIntentRequest = cls._get_default_exit_detect_intent_request(session_id, language_code)
            nlu_response: DetectIntentResponse = nlu_client.services.sessions.detect_intent(request=nlu_request)

        return nlu_response
