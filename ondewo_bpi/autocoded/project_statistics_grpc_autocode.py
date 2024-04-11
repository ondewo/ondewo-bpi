# Copyright 2021-2024 ONDEWO GmbH
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
from ondewo.nlu import common_pb2, project_statistics_pb2
from ondewo.nlu.client import Client
from ondewo.nlu.project_statistics_pb2_grpc import ProjectStatisticsServicer
from ondewo.logging.logger import logger


class AutoProjectStatisticsServicer(ProjectStatisticsServicer):
    """
    [AUTO-GENERATED CLASS]
    generated by: grpc_auto_coder.py
    DO NOT ALTER CODE UNLESS YOU WANT TO DO IT EVERY TIME YOU GENERATE IT!

    used to relay endpoints to the functions defined in:
      >> ./ondewo-nlu-client-python/ondewo/nlu/services/project_statistics.py
    any child class is expected to have a .client attribute to send the service calls to (metaclass-enforced)
    all function/endpoint calls are logged
    override functions if other functionality than a client call is needed

    [original docstring]
    Project Root Statistics

    """
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def client(self) -> Client:
        pass

    def GetIntentCount(self, request: project_statistics_pb2.GetIntentCountRequest, context: grpc.ServicerContext) -> common_pb2.StatResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Returns the intent count within a project

        """
        logger.info("relaying GetIntentCount() to nlu-client...")
        response = self.client.services.project_statistics.get_intent_count(request=request)
        return response

    def GetEntityTypeCount(self, request: project_statistics_pb2.GetEntityTypeCountRequest, context: grpc.ServicerContext) -> common_pb2.StatResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Returns the entity types count within a project

        """
        logger.info("relaying GetEntityTypeCount() to nlu-client...")
        response = self.client.services.project_statistics.get_entity_type_count(request=request)
        return response

    def GetUserCount(self, request: project_statistics_pb2.GetProjectStatRequest, context: grpc.ServicerContext) -> common_pb2.StatResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Returns the users count within a project

        """
        logger.info("relaying GetUserCount() to nlu-client...")
        response = self.client.services.project_statistics.get_user_count(request=request)
        return response

    def GetSessionCount(self, request: project_statistics_pb2.GetProjectStatRequest, context: grpc.ServicerContext) -> common_pb2.StatResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Returns the sessions count within a project

        """
        logger.info("relaying GetSessionCount() to nlu-client...")
        response = self.client.services.project_statistics.get_user_count(request=request)
        return response

    def GetTrainingPhraseCount(self, request: project_statistics_pb2.GetProjectElementStatRequest, context: grpc.ServicerContext) -> common_pb2.StatResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Returns the training phrases count within a project

        """
        logger.info("relaying GetTrainingPhraseCount() to nlu-client...")
        response = self.client.services.project_statistics.get_training_phrase_count(request=request)
        return response

    def GetResponseCount(self, request: project_statistics_pb2.GetProjectElementStatRequest, context: grpc.ServicerContext) -> common_pb2.StatResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Returns the responses count within a project

        """
        logger.info("relaying GetResponseCount() to nlu-client...")
        response = self.client.services.project_statistics.get_training_phrase_count(request=request)
        return response

    def GetEntityValueCount(self, request: project_statistics_pb2.GetProjectElementStatRequest, context: grpc.ServicerContext) -> common_pb2.StatResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Returns the entity value count within a project

        """
        logger.info("relaying GetEntityValueCount() to nlu-client...")
        response = self.client.services.project_statistics.get_training_phrase_count(request=request)
        return response

    def GetEntitySynonymCount(self, request: project_statistics_pb2.GetProjectElementStatRequest, context: grpc.ServicerContext) -> common_pb2.StatResponse:
        """
        [AUTO-GENERATED FUNCTION]
        Returns the entity synonyms count within a project

        """
        logger.info("relaying GetEntitySynonymCount() to nlu-client...")
        response = self.client.services.project_statistics.get_training_phrase_count(request=request)
        return response

# [make flake8 shut up]
