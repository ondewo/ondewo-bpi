import re
import uuid
from typing import (
    Match,
    Optional,
    Pattern,
)

# region API constants based on https://cloud.google.com/apis/design/resource_names
PROJECTS_COLLECTION_ID: str = 'projects'
PROJECT_COLLECTION_ID: str = 'project'
LISTENERS_COLLECTION_ID: str = 'listeners'
CALLERS_COLLECTION_ID: str = 'callers'
SCHEDULED_CALLERS_COLLECTION_ID: str = 'scheduled_callers'
CALLS_COLLECTION_ID: str = 'calls'
INTENTS_COLLECTION_ID: str = 'intents'
# endregion

# region regexes for checking resource names in ONDEWO NLU API
ID_REGEX: str = r'([<>a-zA-Z0-9_\.-]+)'
# UUID_REGEX: str = r'([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})'

# region Project
# projects/<project_id>/project
PROJECT_REGEX: str = rf'{PROJECTS_COLLECTION_ID}/{ID_REGEX}'
PROJECT_PATTERN: Pattern = re.compile(PROJECT_REGEX)
# endregion

# region Listener
# projects/<project_id>/listeners/<listener_id>
LISTENER_REGEX: str = rf'{PROJECTS_COLLECTION_ID}/{ID_REGEX}/{LISTENERS_COLLECTION_ID}/{ID_REGEX}'
LISTENER_PATTERN: Pattern = re.compile(LISTENER_REGEX)
# <code>projects/<project_id>/listeners/<listener_id>/calls/<call_id>
LISTENER_CALL_REGEX: str = rf'/{LISTENER_REGEX}/{CALLS_COLLECTION_ID}/{ID_REGEX}'
LISTENER_CALL_PATTERN: Pattern = re.compile(LISTENER_REGEX)
# endregion

# region Callers
# projects/<project_id>/callers/<caller_id>
CALLER_REGEX: str = rf'{PROJECTS_COLLECTION_ID}/{ID_REGEX}/{CALLERS_COLLECTION_ID}/{ID_REGEX}'
CALLER_PATTERN: Pattern = re.compile(CALLER_REGEX)
# projects/<project_id>/callers/<caller_id>/calls/<call_id>
CALLER_CALL_REGEX: str = rf'/{CALLER_REGEX}/{CALLS_COLLECTION_ID}/{ID_REGEX}'
CALLER_CALL_PATTERN: Pattern = re.compile(CALLER_CALL_REGEX)
# endregion

# region ScheduledCallers
# projects/<project_id>/scheduled_callers/<caller_id>
SCHEDULED_CALLERS_REGEX: str = rf'{PROJECTS_COLLECTION_ID}/{ID_REGEX}/{SCHEDULED_CALLERS_COLLECTION_ID}'
SCHEDULED_CALLERS_PATTERN: Pattern = re.compile(SCHEDULED_CALLERS_REGEX)
# projects/<project_id>/scheduled_callers/<caller_id>/calls/<call_id>
SCHEDULED_CALLERS_CALL_REGEX: str = rf'/{SCHEDULED_CALLERS_REGEX}/{CALLS_COLLECTION_ID}/{ID_REGEX}'
SCHEDULED_CALLERS_CALL_PATTERN: Pattern = re.compile(SCHEDULED_CALLERS_CALL_REGEX)
# endregion

NLU_AGENT_COLLECTION_ID: str = 'agent'
NLU_AGENT_REGEX: str = rf'{PROJECTS_COLLECTION_ID}/{ID_REGEX}/{NLU_AGENT_COLLECTION_ID}'
NLU_AGENT_PATTERN: Pattern = re.compile(NLU_AGENT_REGEX)


# endregion

class OndewoApisUtils:
    """ Class handles the ONDEWO API resource names (https://cloud.google.com/apis/design/resource_names).

    - Generate a resource name in correct format
    - Validate a resource name using a regex
    - Parse a resource name and extract a resource UUID
    """

    @classmethod
    def generate_uuid(cls) -> str:
        """ Generate universally unique identifier in format "bd064098-7d51-4136-9190-44e91057ca20".

        Returns:
            universally unique id
        """
        return str(uuid.uuid4())

    @classmethod
    def generate_project_name(cls, project_id: Optional[str] = None) -> str:
        """ Generate an agent path in format "projects/<project_id>/agent".

        Returns:
            agent path in format "projects/<project_id>/project"
        """
        return f"{PROJECTS_COLLECTION_ID}/{project_id or cls.generate_uuid()}/{PROJECT_COLLECTION_ID}"

    @classmethod
    def search_project_name(cls, name: str) -> Match:
        """ Search for the project name in format "projects/<project_id>/project" in the given resource name.

        Args:
            name: fully-specified resource name in format "projects/<project_id>/project..."

        Returns:
            match object of regex search
        """
        match: Optional[Match] = PROJECT_PATTERN.search(name)
        if match is None:
            raise ValueError(
                f'Given agent name "{name}" has invalid format. '
                f'Required format: "projects/<project_id>/...".'
            )
        return match

    @classmethod
    def get_project_id_from_name(cls, name: str) -> str:
        """ From a path in format "projects/<project_id>/project..." get the "<project_id>".

        Args:
            name: full resource name in format "projects/<project_id>/project..."

        Returns:
            project id
        """
        match: Match = cls.search_project_name(name)
        project_id: str = match.group(1)
        return project_id

    @classmethod
    def get_project_name_from_resource_name(cls, name: str) -> str:
        """ From a path in format "projects/<project_id>/project..." get the part before the "..."

        Args:
            name: fully-specified resource name in format "projects/<project_id>/project..."

        Returns:
            agent path in format "projects/<project_id>/project"
        """
        match: Match = cls.search_project_name(name=name)
        projects_path: str = match.group()
        return projects_path + "/" + "project"

    @staticmethod
    def get_last_uuid_from_path(name: str) -> str:
        """ Extract the last resource uuid from the full path.

        Examples:
            "projects/project_1/agent/sessions/123" -> "123"
            "projects/project_1/agent/sessions/123/reviews/456" -> "456"

        Args:
            name: full name in format "projects/<project_id>/project/.../<id>"

        Returns:
            last resource uuid of the path
        """
        return name.rsplit('/', maxsplit=1)[-1]

    @classmethod
    def generate_listener_name(cls, project_id: str, listener_id: Optional[str] = None) -> str:
        """ Generate a listener name

        Returns:
            listener name in format projects/<project_id>/listeners/<listener_id>
        """
        listeners_name: str = f"{PROJECTS_COLLECTION_ID}/{project_id}/{LISTENERS_COLLECTION_ID}"
        return f"{listeners_name}/{listener_id or cls.generate_uuid()}"

    @classmethod
    def generate_listeners_call_name(cls, project_id: str, listener_id: str, call_id: Optional[str] = None) -> str:
        """ Generate a call name of a listener

        Returns:
            call name of a listener in format projects/<project_id>/listeners/<listener_id>/call/<call_id>
        """
        listener_name: str = f"{PROJECTS_COLLECTION_ID}/{project_id}/{LISTENERS_COLLECTION_ID}/{listener_id}"
        return f"{listener_name}/{CALLS_COLLECTION_ID}/{call_id or cls.generate_uuid()}"

    @classmethod
    def generate_caller_name(cls, project_id: str, caller_id: Optional[str] = None) -> str:
        """ Generate a caller name

        Returns:
            caller name in format projects/<project_id>/callers/<caller_id>
        """
        callers_name: str = f"{PROJECTS_COLLECTION_ID}/{project_id}/{CALLERS_COLLECTION_ID}"
        return f"{callers_name}/{caller_id or cls.generate_uuid()}"

    @classmethod
    def generate_callers_call_name(cls, project_id: str, caller_id: str, call_id: Optional[str] = None) -> str:
        """ Generate a call name of a caller

        Returns:
            call name of a caller in format projects/<project_id>/callers/<caller_id>/call/<call_id>
        """
        callers_name: str = f"{PROJECTS_COLLECTION_ID}/{project_id}/{CALLERS_COLLECTION_ID}/{caller_id}"
        return f"{callers_name}/{CALLS_COLLECTION_ID}/{call_id or cls.generate_uuid()}"

    @classmethod
    def search_caller_name(cls, name: str) -> Match:
        """ Search for the caller name in format "projects/<project_id>/callers/<caller_id>" in the given resource name.

        Args:
            name: fully-specified resource name in format "projects/<project_id>/callers/<caller_id>/..."

        Returns:
            match object of regex search
        """
        match: Optional[Match] = CALLER_PATTERN.search(name)
        if match is None:
            raise ValueError(
                f'Given agent name "{name}" has invalid format. '
                f'Required format: "projects/<project_id>/callers/<caller_id>/...".'
            )
        return match

    @classmethod
    def get_caller_id_from_name(cls, name: str) -> str:
        """ From a path in format "projects/<project_id>/callers/<caller_id>..." get the "<caller_id>".

        Args:
            name: full resource name in format "projects/<project_id>/callers/<caller_id>..."

        Returns:
            caller id
        """
        match: Match = cls.search_caller_name(name)
        caller_id: str = match.group(2)
        return caller_id

    @classmethod
    def search_listener_name(cls, name: str) -> Match:
        """ Search for the listener name in format "projects/<project_id>/listeners/<listener_id>" in the given
        resource name.

        Args:
            name: fully-specified resource name in format "projects/<project_id>/listeners/<listener_id>..."

        Returns:
            match object of regex search
        """
        match: Optional[Match] = LISTENER_PATTERN.search(name)
        if match is None:
            raise ValueError(
                f'Given agent name "{name}" has invalid format. '
                f'Required format: "projects/<project_id>/listeners/<listener_id>...".'
            )
        return match

    @classmethod
    def get_listener_id_from_name(cls, name: str) -> str:
        """ From a path in format "projects/<project_id>/listeners/<listener_id>..." get the "<listener_id>".

        Args:
            name: full resource name in format "projects/<project_id>/listeners/<listener_id>..."

        Returns:
            listener id
        """
        match: Match = cls.search_listener_name(name)
        listener_id: str = match.group(2)
        return listener_id

    @classmethod
    def get_caller_name_from_resource_name(cls, name: str) -> str:
        """ From a path in format "projects/<project_id>/callers/<caller_id>..." get the part before the "..."

        Args:
            name: fully-specified resource name in format "projects/<project_id>/callers/<caller_id>..."

        Returns:
            agent path in format "projects/<project_id>/project"
        """
        match: Match = cls.search_caller_name(name=name)
        path: str = match.group()
        return path

    @classmethod
    def get_listener_name_from_resource_name(cls, name: str) -> str:
        """ From a path in format "projects/<project_id>/listeners/<listener_id>..." get the part before the "..."

        Args:
            name: fully-specified resource name in format "projects/<project_id>/listeners/<listener_id>..."

        Returns:
            agent path in format "projects/<project_id>/project"
        """
        match: Match = cls.search_listener_name(name=name)
        path: str = match.group()
        return path

    @classmethod
    def search_agent_path(cls, path: str) -> Match:
        """ Search for the agent name in format "projects/<project_id>/agent" in the given resource name.

        Args:
            path: fully-specified resource name in format "projects/<project_id>/agent..."

        Returns:
            match object of regex search
        """
        match: Optional[Match] = NLU_AGENT_PATTERN.search(path)
        if match is None:
            raise ValueError(
                f'Given agent name "{path}" has invalid format. '
                f'Required format: "projects/<Agent ID>/agent/...".'
            )
        return match

    @classmethod
    def get_nlu_agent_id_from_name(cls, name: str) -> str:
        """ From a path in format "projects/<project_id>/project..." get the "<project_id>".

        Args:
            name: full resource name in format "projects/<project_id>/project..."

        Returns:
            project id
        """
        match: Match = cls.search_agent_path(name)
        project_id: str = match.group(1)
        return project_id

    @classmethod
    def generate_nlu_intent_name(cls, agent_name: str, intent_id: Optional[str] = None) -> str:
        """ Get full intent path.

        Examples:
            "project_1" -> "projects/project_1/agent/intents/010b906e-db57-491f-bbcf-0e9a3d83d15a"
            ("project_1", "some_intent") -> "projects/project_1/agent/intents/some_intent"

        Args:
            project_id (str): project ID
            intent_id (Optional[str]): optional intent UUID

        Returns:
            full intent path
        """
        return f'{agent_name}/{INTENTS_COLLECTION_ID}/{intent_id or cls.generate_uuid()}'

    @classmethod
    def generate_nlu_agent_name(cls, agent_id: Optional[str] = None) -> str:
        """ Get full agent name.

        Examples:
            "agent_id" -> "projects/agent_id/agent/"

        Args:
            agent_id (str): agent ID


        Returns:
            full intent path
        """
        return f'{PROJECTS_COLLECTION_ID}/{agent_id or cls.generate_uuid()}/{NLU_AGENT_COLLECTION_ID}'

    @staticmethod
    def is_listener(name: str) -> bool:
        """
        Checks if the given name matches the pattern of a listener.

        Args:
            name (str): The name to check.

        Returns:
            bool: True if the name is a listener, False otherwise.

        Example:
            is_listener = CustomDockerClient.is_listener("listener_container")
        """
        return LISTENER_PATTERN.search(name) is not None

    @staticmethod
    def is_caller(name: str) -> bool:
        """
        Checks if the given name matches the pattern of a caller.

        Args:
            name (str): The name to check.

        Returns:
            bool: True if the name is a caller, False otherwise.

        Example:
            is_caller = CustomDockerClient.is_caller("caller_container")
        """
        return CALLER_PATTERN.search(name) is not None
