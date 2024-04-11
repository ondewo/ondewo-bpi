import re
from re import (
    Match,
    Pattern,
)
from typing import Optional


class ContextHelper:
    AGENT_PATTERN: Pattern = re.compile(r'projects/([a-zA-Z\d_.-]+)/agent')

    @classmethod
    def get_agent_path_from_path(cls, path: str) -> str:
        """ From a path in format "projects/<project_id>/agent..." get the part before the "..."

        Args:
            path: fully-specified resource name in format "projects/<project_id>/agent..."

        Returns:
            agent path in format "projects/<project_id>/agent"
        """
        match: Optional[Match] = cls.AGENT_PATTERN.search(path)
        if match is None:
            raise ValueError(
                f'Given agent name "{path}" has invalid format. '
                'Required format: "projects/<Project ID>/agent/...".'
            )
        agent_path: str = match.group()
        return agent_path

    @classmethod
    def get_last_uuid_from_path(cls, path: str) -> str:
        """ Extract the last resource uuid from the full path.

        Examples:
            "projects/project_1/agent/sessions/123" -> "123"
            "projects/project_1/agent/sessions/123/reviews/456" -> "456"

        Args:
            path: full DFv2 name in format "projects/<project_id>/agent/.../<uuid>"

        Returns:
            last resource uuid of the path
        """
        return path.rsplit('/', maxsplit=1)[-1]


if __name__ == '__main__':
    print(
        f'should match: {ContextHelper.get_agent_path_from_path("projects/9c4e97ab-13ec-4b4b-bade-256b5c6e1bb2/agent/sessions/9c4e97ab-13ec-4b4b-bade-256b5c6e1bb2")}'
    )
    print(
        f'should match: {ContextHelper.get_agent_path_from_path("projects/9c4e97ab-13ec-4b4b-bade-256b5c6e1bb2/agent/sessions/")}'
    )
    print(
        f'should match: {ContextHelper.get_agent_path_from_path("projects/9c4e97ab-13ec-4b4b-bade-256b5c6e1bb2/agent")}'
    )
    print(
        f'should NOT match: {ContextHelper.get_agent_path_from_path("projects/9c4e97ab-13ec-4b4b-bade-256b5c6e1bb2")}'
    )
    print(f'should NOT match: {ContextHelper.get_agent_path_from_path("9c4e97ab-13ec-4b4b-bade-256b5c6e1bb2")}')
