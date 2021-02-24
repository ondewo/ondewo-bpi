# Copyright 2021 ONDEWO GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# [AUTO-GENERATED FILE]

from abc import ABCMeta, abstractmethod

import grpc
from google.longrunning.operations_grpc_pb2 import Operation
from google.protobuf.empty_pb2 import Empty
from ondewo.nlu import agent_pb2
from ondewo.nlu.client import Client
from ondewo.nlu.agent_pb2_grpc import AgentsServicer
from ondewologging.logger import logger


class AutoAgentsServicer(AgentsServicer):
    """
    [AUTO-GENERATED CLASS]
    generated by: grpc_auto_coder.py
    DO NOT ALTER CODE UNLESS YOU WANT TO DO IT EVERY TIME YOU GENERATE IT!

    used to relay endpoints to the functions defined in:
      >> ./ondewo-nlu-client-python/ondewo/nlu/services/agents.py
    any child class is expected to have a .client attribute to send the service calls to (metaclass-enforced)
    all function/endpoint calls are logged
    override functions if other functionality than a client call is needed

    [original docstring]
    Agents are best described as Natural Language Understanding (NLU) modules

    """
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> Client:
        pass

    def CreateAgent(self, request: agent_pb2.CreateAgentRequest, context: grpc.ServicerContext) -> agent_pb2.Agent:
        """
        [AUTO-GENERATED FUNCTION]
        Creates the specified agent.

        """
        logger.info("relaying CreateAgent() to nlu-client...")
        response = self.client.services.agents.create_agent(request=request)
        return response

    def UpdateAgent(self, request: agent_pb2.UpdateAgentRequest, context: grpc.ServicerContext) -> agent_pb2.Agent:
        """
        [AUTO-GENERATED FUNCTION]
        Updates the specified agent.

        """
        logger.info("relaying UpdateAgent() to nlu-client...")
        response = self.client.services.agents.update_agent(request=request)
        return response

    def GetAgent(self, request: agent_pb2.GetAgentRequest, context: grpc.ServicerContext) -> agent_pb2.Agent:
        """
        [AUTO-GENERATED FUNCTION]
        Retrieves the specified agent.

        """
        logger.info("relaying GetAgent() to nlu-client...")
        response = self.client.services.agents.get_agent(request=request)
        return response

    def DeleteAgent(self, request: agent_pb2.DeleteAgentRequest, context: grpc.ServicerContext) -> Empty:
        """
        [AUTO-GENERATED FUNCTION]
        Deletes the specified agent.

        """
        logger.info("relaying DeleteAgent() to nlu-client...")
        response = self.client.services.agents.delete_agent(request=request)
        return response

    def DeleteAllAgents(self, request: Empty, context: grpc.ServicerContext) -> Empty:
        """
        [AUTO-GENERATED FUNCTION]
        Deletes all agents in the server (for development purposes only).

        """
        logger.info("relaying DeleteAllAgents() to nlu-client...")
        response = self.client.services.agents.delete_all_agents()
        return response

    def ListAgents(self, request: agent_pb2.ListAgentsRequest, context: grpc.ServicerContext) -> agent_pb2.ListAgentsResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Lists agents in the server associated to the current user

        """
        logger.info("relaying ListAgents() to nlu-client...")
        response = self.client.services.agents.list_agents(request=request)
        return response

    def ListAgentsOfUser(self, request: agent_pb2.ListAgentsRequest, context: grpc.ServicerContext) -> agent_pb2.ListAgentsOfUserResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Lists agents in the server associated to the given user

        """
        logger.info("relaying ListAgentsOfUser() to nlu-client...")
        response = self.client.services.agents.list_agents_of_user(request=request)
        return response

    def ListAllAgents(self, request: agent_pb2.ListAgentsRequest, context: grpc.ServicerContext) -> agent_pb2.ListAgentsResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Lists all agents in the server

        """
        logger.info("relaying ListAllAgents() to nlu-client...")
        response = self.client.services.agents.list_agents(request=request)
        return response

    def AddUserToProject(self, request: agent_pb2.AddUserToProjectRequest, context: grpc.ServicerContext) -> Empty:
        """
        [AUTO-GENERATED FUNCTION]
        Adds a user with specified id to the project (agent)

        """
        logger.info("relaying AddUserToProject() to nlu-client...")
        response = self.client.services.agents.add_user_to_project(request=request)
        return response

    def RemoveUserFromProject(self, request: agent_pb2.RemoveUserFromProjectRequest, context: grpc.ServicerContext) -> Empty:
        """
        [AUTO-GENERATED FUNCTION]
        Removes a user with specified id from the project (agent)

        """
        logger.info("relaying RemoveUserFromProject() to nlu-client...")
        response = self.client.services.agents.remove_user_from_project(request=request)
        return response

    def ListUsersInProject(self, request: agent_pb2.ListUsersInProjectRequest, context: grpc.ServicerContext) -> agent_pb2.ListUsersInProjectResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying ListUsersInProject() to nlu-client...")
        response = self.client.services.agents.list_users_in_project(request=request)
        return response

    def GetPlatformInfo(self, request: Empty, context: grpc.ServicerContext) -> agent_pb2.GetPlatformInfoResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying GetPlatformInfo() to nlu-client...")
        response = self.client.services.agents.get_platform_info()
        return response

    def ListProjectPermissions(self, request: agent_pb2.ListProjectPermissionsRequest, context: grpc.ServicerContext) -> agent_pb2.ListProjectPermissionsResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying ListProjectPermissions() to nlu-client...")
        response = self.client.services.agents.list_project_permissions(request=request)
        return response

    def TrainAgent(self, request: agent_pb2.TrainAgentRequest, context: grpc.ServicerContext) -> Operation:
        """
        [AUTO-GENERATED FUNCTION]
        Trains the specified agent.

        """
        logger.info("relaying TrainAgent() to nlu-client...")
        response = self.client.services.agents.train_agent(request=request)
        return response

    def BuildCache(self, request: agent_pb2.BuildCacheRequest, context: grpc.ServicerContext) -> Operation:
        """
        [AUTO-GENERATED FUNCTION]
        Builds cache for the specified agent.

        """
        logger.info("relaying BuildCache() to nlu-client...")
        response = self.client.services.agents.build_cache(request=request)
        return response

    def ExportAgent(self, request: agent_pb2.ExportAgentRequest, context: grpc.ServicerContext) -> Operation:
        """
        [AUTO-GENERATED FUNCTION]
        Exports the specified agent to a ZIP file.

        """
        logger.info("relaying ExportAgent() to nlu-client...")
        response = self.client.services.agents.export_agent(request=request)
        return response

    def ImportAgent(self, request: agent_pb2.ImportAgentRequest, context: grpc.ServicerContext) -> Operation:
        """
        [AUTO-GENERATED FUNCTION]
        Imports the specified agent from a ZIP file.

        """
        logger.info("relaying ImportAgent() to nlu-client...")
        response = self.client.services.agents.import_agent(request=request)
        return response

    def OptimizeRankingMatch(self, request: agent_pb2.OptimizeRankingMatchRequest, context: grpc.ServicerContext) -> Operation:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying OptimizeRankingMatch() to nlu-client...")
        response = self.client.services.agents.optimize_ranking_match(request=request)
        return response

    def RestoreAgent(self, request: agent_pb2.RestoreAgentRequest, context: grpc.ServicerContext) -> Operation:
        """
        [AUTO-GENERATED FUNCTION]
        Restores the specified agent from a ZIP file.

        """
        logger.info("relaying RestoreAgent() to nlu-client...")
        response = self.client.services.agents.restore_agent(request=request)
        return response

    def GetAgentStatistics(self, request: agent_pb2.GetAgentStatisticsRequest, context: grpc.ServicerContext) -> agent_pb2.GetAgentStatisticsResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying GetAgentStatistics() to nlu-client...")
        response = self.client.services.agents.get_agent_statistics(request=request)
        return response

    def SetAgentStatus(self, request: agent_pb2.SetAgentStatusRequest, context: grpc.ServicerContext) -> agent_pb2.Agent:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying SetAgentStatus() to nlu-client...")
        response = self.client.services.agents.set_agent_status(request=request)
        return response

    def SetResources(self, request: agent_pb2.SetResourcesRequest, context: grpc.ServicerContext) -> Empty:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying SetResources() to nlu-client...")
        response = self.client.services.agents.set_resources(request=request)
        return response

    def DeleteResources(self, request: agent_pb2.DeleteResourcesRequest, context: grpc.ServicerContext) -> Empty:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying DeleteResources() to nlu-client...")
        response = self.client.services.agents.delete_resources(request=request)
        return response

    def ExportResources(self, request: agent_pb2.ExportResourcesRequest, context: grpc.ServicerContext) -> agent_pb2.ExportResourcesResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Missing associated documentation comment in .proto file.
        """
        logger.info("relaying ExportResources() to nlu-client...")
        response = self.client.services.agents.export_resources(request=request)
        return response

# [make flake8 shut up]
