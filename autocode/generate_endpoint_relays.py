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
from dataclasses import dataclass
from typing import (
    List,
)

from autocode.client_type import ClientType
from autocode.grpc_auto_coder import GRPCAutoCoder


# TODO: Make it dynamic so it reads from the file system

@dataclass
class ProtoData:
    in_file: str
    out_file: str
    proto_file: str
    client_file: str
    client_type: ClientType


proto_data_list_to_generate: List[ProtoData] = [
    # region proto data
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/agent_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/agent_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/agent.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/agents.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/aiservices_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/aiservices_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/aiservices.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/aiservices.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/ccai_project_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/ccai_project_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/ccai_project.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/ccai_projects.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/context_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/context_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/context.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/contexts.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/entity_type_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/entity_type_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/entity_type.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/entity_types.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/intent_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/intent_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/intent.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/intents.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/operations_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/operations_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/operations.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/operations.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/project_role_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/project_role_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/project_role.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/project_roles.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/project_statistics_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/project_statistics_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/project_statistics.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/project_statistics.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/server_statistics_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/server_statistics_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/server_statistics.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/server_statistics.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/session_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/session_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/session.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/sessions.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/user_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/user_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/user.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/users.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/nlu/utility_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/utility_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/nlu/utility.proto",
        client_file="./ondewo-nlu-client-python/ondewo/nlu/services/utilities.py",
        client_type=ClientType.NLU,
    ),
    ProtoData(
        in_file="./ondewo-nlu-client-python/ondewo/qa/qa_pb2_grpc.py",
        out_file="./ondewo_bpi/autocoded/qa_grpc_autocode.py",
        proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/qa/qa.proto",
        client_file="./ondewo-nlu-client-python/ondewo/qa/services/qa.py",
        client_type=ClientType.QA,
    ),
    # endregion proto data
]
# Note: not needed
# ProtoData(
#     in_file="./ondewo-nlu-client-python/ondewo/webhook/webhook_pb2_grpc.py",
#     out_file="./ondewo_bpi/autocoded/webhook_grpc_autocode.py",
#     proto_file="./ondewo-nlu-client-python/ondewo-nlu-api/ondewo/webhook/webhook.proto",
#     client_file="./ondewo-nlu-client-python/ondewo/webhook/services/webhook.py",
#     client_type=ClientType.QA,
# ),

if __name__ == "__main__":

    for proto_data in proto_data_list_to_generate:
        coder: GRPCAutoCoder = GRPCAutoCoder(
            in_file=proto_data.in_file,
            out_file=proto_data.out_file,
            proto_file=proto_data.proto_file,
            client_file=proto_data.client_file,
            client_type=proto_data.client_type,
        )
        coder.generate_code()
