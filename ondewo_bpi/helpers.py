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
import csv
import errno
import glob
import io
import json
import os
import pickle
import re
import shutil
import stat
from pathlib import Path
from time import (
    sleep,
    time,
)
from typing import (
    Dict,
    List,
    Match,
    Pattern,
    Tuple,
    TypeVar,
)

import pandas as pd
import six
from grpc._channel import _InactiveRpcError  # noqa
from ondewo.logging.decorators import Timer
from ondewo.nlu import (
    context_pb2,
    session_pb2,
)
from ondewo.nlu.client import Client
from py._path.local import LocalPath  # noqa

T = TypeVar("T")

UUID4_RGX: str = r'[^\W_]{8}-[^\W_]{4}-[^\W_]{4}-[^\W_]{4}-[^\W_]{12}'
URL_REGEX: Pattern = re.compile(r'http://|https://|ftp://|file://|file:\\')
DECAY_FUNCTION_TIME: str = 'time'
DECAY_FUNCTION_INTERACTION: str = 'interaction'

from typing import (
    Any,
    Optional,
    Set,
    Union,
)

from google.protobuf.internal.containers import MessageMap
from google.protobuf.message import Message
from google.protobuf.struct_pb2 import Struct
from google.protobuf.type_pb2 import Enum
from ondewo.logging.logger import logger_console as log

CREATED_BY_MODIFIED_BY_CREATED_AT_MODIFIED_AT_SET: Set[str] = {'created_by', 'modified_by', 'created_at', 'modified_at'}


@Timer(
    logger=log.debug, log_arguments=False,
    message='BPI helpers.py: add_params_to_cai_context: Elapsed time: {:0.4f}'
)
def add_params_to_cai_context(
    client: Client,
    response: session_pb2.DetectIntentResponse,
    params: Dict[str, Union[str, float, int, bool, context_pb2.Context.Parameter]],
    context: str,
) -> Dict[str, context_pb2.Context.Parameter]:
    return _add_params_to_cai_context(
        client=client,
        session=get_session_from_response(response),
        params=params,
        context=context,
    )


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: _add_params_to_cai_context: Elapsed time: {:0.4f}'
)
def _add_params_to_cai_context(
    client: Client,
    session: str,
    params: Dict[str, Union[str, float, int, bool, context_pb2.Context.Parameter]],
    context: str,
) -> Dict[str, context_pb2.Context.Parameter]:
    log.info(
        {
            "message": "adding parameter to cai",
            "parameter": params,
            "context": context,
            "tags": ["parameters", "contexts"],
        }
    )
    parameters = create_parameter_dict(parameter_dict=params)
    try:
        request = context_pb2.GetContextRequest(name=f"{session}/contexts/{context}")
        existing_context = client.services.contexts.get_context(request=request)
        for k, v in parameters.items():
            existing_context.parameters[k].CopyFrom(v)

        # clear metadata
        existing_context.ClearField("created_at")
        existing_context.ClearField("modified_at")
        existing_context.ClearField('created_by')
        existing_context.ClearField('modified_by')
        client.services.contexts.update_context(request=context_pb2.UpdateContextRequest(context=existing_context))

    except _InactiveRpcError:
        context = context_pb2.Context(
            name=f"{session}/contexts/{context}",
            lifespan_count=100,
            parameters=parameters,
            lifespan_time=1000,
        )
        context.ClearField("created_at")
        context.ClearField("modified_at")
        context.ClearField('created_by')
        context.ClearField('modified_by')
        client.services.contexts.create_context(
            request=context_pb2.CreateContextRequest(session_id=f'{session}', context=context)
        )

    return parameters


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: delete_param_from_cai_context: Elapsed time: {:0.4f}'
)
def delete_param_from_cai_context(
    client: Client,
    response: session_pb2.DetectIntentResponse,
    param_name: str,
    context: str
) -> None:
    log.info(
        {
            "message": "deleting parameter from cai",
            "parameter": param_name,
            "context": context,
            "tags": ["parameters", "contexts"],
        }
    )
    session: str = get_session_from_response(response=response)
    context_name: str = f"{session}/contexts/{context}"
    existing_context: context_pb2.Context = client.services.contexts.get_context(
        request=context_pb2.GetContextRequest(name=context_name),
    )
    try:
        del existing_context.parameters[param_name]
        client.services.contexts.delete_context(request=context_pb2.DeleteContextRequest(name=context_name))
        client.services.contexts.create_context(
            request=context_pb2.CreateContextRequest(session_id=session, context=existing_context)
        )
    except KeyError:
        log.exception(
            {
                "message": "tried to delete param that didnt exist",
                "parameter": param_name,
                "context": context,
                "tags": ["parameters", "contexts"],
            }
        )


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: detect_intent: Elapsed time: {:0.4f}'
)
def detect_intent(
    client: Client,
    response: session_pb2.DetectIntentResponse,
    text: str
) -> session_pb2.DetectIntentResponse:
    log.info({"message": "detect intent triggered in bpi helpers", "tags": ["timing"]})
    request: session_pb2.DetectIntentRequest = get_detect_intent_request(
        text=text,
        session=get_session_from_response(response=response),
    )
    log.info({"message": "detect intent returned in bpi helpers", "tags": ["timing"]})
    result: session_pb2.DetectIntentResponse = client.services.sessions.detect_intent(request)
    log.info(f"wrote {text}, received {result.query_result.fulfillment_messages}")
    return result


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: get_detect_intent_request: Elapsed time: {:0.4f}'
)
def get_detect_intent_request(
    session: str,
    text: str,
    language: str = 'de-DE',
    query_params: Optional[session_pb2.QueryParameters] = None
) -> session_pb2.DetectIntentRequest:
    request: session_pb2.DetectIntentRequest = session_pb2.DetectIntentRequest(
        session=session,
        query_input=session_pb2.QueryInput(
            text=session_pb2.TextInput(text=text, language_code=language)
        ),
        query_params=query_params,
    )
    return request


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: create_parameter_dict: Elapsed time: {:0.4f}'
)
def create_parameter_dict(
    parameter_dict: Dict[str, Union[str, float, int, bool, context_pb2.Context.Parameter]],
) -> Optional[Dict[str, context_pb2.Context.Parameter]]:
    assert isinstance(parameter_dict, dict) or parameter_dict is None, "parameter must be a dict or None"

    # if parameter_dict is not None:
    #     context_dict: Dict[str, context_pb2.Context.Parameter] = {
    #         key: context_pb2.Context.Parameter(
    #             display_name=key,
    #             value=parameter_dict[key],
    #             value_original=parameter_dict[key],
    #         )
    #         for key in parameter_dict
    #     }
    #     return context_dict

    if parameter_dict is not None:
        context_dict: Dict[str, context_pb2.Context.Parameter] = {}
        for key in parameter_dict:
            if isinstance(parameter_dict[key], context_pb2.Context.Parameter):
                # if it is already a parameter, then just add it to the context
                context_dict[key] = parameter_dict[key]
            else:
                # if it is a value then create a parameter object from it
                context_dict[key] = context_pb2.Context.Parameter(
                    display_name=key,
                    value=parameter_dict[key],
                    value_original=parameter_dict[key],
                )

        return context_dict

    return None


# This function creates a detect intent request that will trigger a specific intent
#   using the 'exact intent' trigger
@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: trigger_intent: Elapsed time: {:0.4f}'
)
def trigger_intent(
    client: Client,
    session: str,
    intent_name: str,
    language: str = "de",
    additional_contexts: Optional[List[context_pb2.Context]] = None,
) -> session_pb2.DetectIntentResponse:
    """
    Trigger a specific intent in the NLU backend without intent matching.

    Args:
        client: nlu client
        session: full session to perform the trigger in ('parent/<PROJECT_ID>/agent/sessions/<SESSION_ID>')
        intent_name: intent that you want to trigger
        language: language of the project
        additional_contexts: if you want to add additional contexts to the session

    Returns:
        session_pb2.DetectIntentResponse
    """
    if not additional_contexts:
        additional_contexts = []

    log.info({"message": "triggering specific intent", "intent_name": intent_name})
    trigger_context: context_pb2.Context = create_context(
        context=f"{session}/contexts/exact_intent",
        parameters=create_parameter_dict({"intent_name": intent_name}),
        lifespan_count=1,
    )
    request: session_pb2.DetectIntentRequest = get_detect_intent_request(
        text=f"Triggering Specific Intent: {intent_name}",
        session=session,
        language=language,
        query_params=session_pb2.QueryParameters(contexts=[trigger_context, *additional_contexts]),
    )
    result: session_pb2.DetectIntentResponse = client.services.sessions.detect_intent(request)
    log.info(f"triggered {intent_name}")
    return result


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: create_context_struct: Elapsed time: {:0.4f}'
)
def create_context(
    context: str,
    parameters: Optional[Dict[str, context_pb2.Context.Parameter]],
    lifespan_count: int = 5,
) -> context_pb2.Context:
    context_proto: context_pb2.Context = context_pb2.Context(
        name=f"{context}",
        lifespan_count=lifespan_count,
        parameters=parameters,
    )
    return context_proto


# This function deletes periods from the text in a request
@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: strip_final_periods_from_request: Elapsed time: {:0.4f}'
)
def strip_final_periods_from_request(request: session_pb2.DetectIntentRequest) -> session_pb2.DetectIntentRequest:
    request.query_input.text.text = request.query_input.text.text.strip(".")
    return request


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: get_session_from_response: Elapsed time: {:0.4f}'
)
def get_session_from_response(response: session_pb2.DetectIntentResponse) -> str:
    return response.query_result.diagnostic_info["sessionId"]  # type: ignore


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: remove_dir: Elapsed time: {:0.4f}'
)
def remove_dir(dir_path: str, exception: bool = True) -> None:
    """Removes a directory.
    Succeeds even if the path does not exist anymore."""
    if is_dir(dir_path):
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)
        except OSError as e:
            if exception and e.errno != errno.EEXIST:
                raise

    # check that the dir_path now indeed does not exist anymore
    is_not_dir(dir_path=dir_path, exception=exception)


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: remove_dir_for_file_path: Elapsed time: {:0.4f}'
)
def remove_dir_for_file_path(file_path: Union[str, LocalPath]) -> None:
    """Removes directory recursively for files path."""
    if os.path.isdir(file_path):
        try:
            shutil.rmtree(file_path)
        except OSError:
            try:
                # change read-only permission to write permission for deletion
                os.chmod(file_path, stat.S_IWRITE)
                shutil.rmtree(file_path)
            except OSError:
                try:
                    # delete directory incl. files without errors
                    shutil.rmtree(file_path, ignore_errors=True)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: remove_file_for_file_path: Elapsed time: {:0.4f}'
)
def remove_file_for_file_path(file_path: Union[str, LocalPath], exception: bool = True) -> None:
    """Removes the file at filepath."""
    if is_file(file_path, exception=exception):
        try:
            os.remove(file_path)
        except OSError as e:
            if exception:
                raise e


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: create_dir_for_file_path: Elapsed time: {:0.4f}'
)
def create_dir_for_file_path(file_path: Union[str, LocalPath]) -> None:
    """Create directories for files path."""
    try:
        os.makedirs(os.path.dirname(file_path))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: relative_normpath: Elapsed time: {:0.4f}'
)
def relative_normpath(f: Optional[str], path: Union[str, LocalPath]) -> Optional[str]:
    """Return the path of file relative to `path`."""
    if f is not None:
        return os.path.normpath(os.path.relpath(f, path))
    else:
        return None


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: create_dir: Elapsed time: {:0.4f}'
)
def create_dir(dir_path: Union[str, LocalPath], exception: bool = True) -> None:
    """Creates a directory and its super paths.
    Succeeds even if the path already exists."""
    if not is_dir(dir_path):
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        except OSError as e:
            if exception and e.errno != errno.EEXIST:
                raise

    # check that the dir_path now indeed exists as a directory
    is_dir(dir_path, exception=exception)


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: create_dir_for_file: Elapsed time: {:0.4f}'
)
def create_dir_for_file(file_path: Union[str, LocalPath]) -> Optional[str]:
    """Creates any missing parent directories of this files path."""
    try:
        dir_path: str = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return None


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: list_directory: Elapsed time: {:0.4f}'
)
def list_directory(path: Union[str, LocalPath]) -> List[str]:
    """Returns all files and folders excluding hidden files.
    If the path points to a file, returns the file. This is a recursive
    implementation returning files in any depth of the path."""

    if not isinstance(path, six.string_types) and not isinstance(path, bytes):
        raise ValueError("Resource name must be a string or bytes type")

    path = str(path)
    if os.path.isfile(path):
        return [path]
    elif os.path.isdir(path):

        results: List[str] = []
        for base, dirs, files in os.walk(path):
            # remove hidden files
            ok_files = filter(lambda x: not x.startswith('.'), files)
            results.extend(os.path.join(base, f) for f in ok_files)
        return results
    else:
        raise ValueError(
            "Could not locate the resource '{}'."
            "".format(os.path.abspath(path))
        )


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: list_files: Elapsed time: {:0.4f}'
)
def list_files(path: Union[str, LocalPath]) -> List[str]:
    """Returns all files excluding hidden files.
    If the path points to a file, returns the file."""
    return [fn for fn in list_directory(path) if os.path.isfile(fn)]


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: list_subdirectories: Elapsed time: {:0.4f}'
)
def list_subdirectories(path: Union[str, LocalPath]) -> List[str]:
    """Returns all folders excluding hidden files.
     If the path points to a file, returns an empty list."""
    return [fn for fn in glob.glob(os.path.join(path, '*')) if os.path.isdir(fn)]


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: list_to_str: Elapsed time: {:0.4f}'
)
def list_to_str(l: List[str], delim: str = ", ", quote: str = "'") -> str:  # noqa
    return delim.join([quote + e + quote for e in l])


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: is_file: Elapsed time: {:0.4f}'
)
def is_file(
    file_path: Union[str, LocalPath],
    exception: bool = False,
    timeout: float = 0.0,
    step: float = 0.1,
) -> bool:
    start_time: float = time()
    file_exists: bool = os.path.isfile(file_path)

    if exception and not file_exists:
        raise FileNotFoundError(file_path)

    # retry if file does not exist until timout
    retries: int = 0
    while not file_exists and time() < (start_time + timeout):
        retries = retries + 1
        log.debug(f"is_file: current retry: {retries} for file: {file_path} ")
        sleep(step)
        file_exists = os.path.isfile(file_path)

    return file_exists


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: is_not_dir: Elapsed time: {:0.4f}'
)
def is_not_dir(dir_path: Union[str, LocalPath], exception: object = False) -> bool:
    dir_exists: bool = os.path.isdir(dir_path)
    if exception and dir_exists:
        raise IsADirectoryError(dir_path)
    return dir_exists


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: is_dir: Elapsed time: {:0.4f}'
)
def is_dir(dir_path: Union[str, LocalPath], exception: bool = False) -> bool:
    dir_exists: bool = os.path.isdir(dir_path)
    if exception and not dir_exists:
        raise NotADirectoryError(dir_path)
    return dir_exists


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: json_to_string: Elapsed time: {:0.4f}'
)
def json_to_string(json_dict: Any, indent: int = 4, ensure_ascii: bool = False, **kwargs: Any) -> str:
    return json.dumps(json_dict, indent=indent, ensure_ascii=ensure_ascii, **kwargs)


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: write_json_to_file: Elapsed time: {:0.4f}'
)
def write_json_to_file(file_path: Union[str, LocalPath], json_dict: Any, **kwargs: Any) -> Any:
    """Write an object as a json string to a file."""
    write_text_to_file(file_path, json_to_string(json_dict, **kwargs))
    return json_dict


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: write_pb_message_to_file: Elapsed time: {:0.4f}'
)
def write_pb_message_to_file(file_path: Union[str, LocalPath], message: Message) -> None:
    # create dir if necessary
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(message.SerializeToString())


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: write_text_to_file: Elapsed time: {:0.4f}'
)
def write_text_to_file(file_path: Union[str, LocalPath], text: str) -> str:
    """
    Write a text to a file.
    Note: If the file exists, this function overrides the existing file.
    """
    if is_file(file_path):
        log.warning(f'Text file "{file_path}" already exits, therefore, it will be overridden.')

    dir_path: str = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with io.open(file_path, 'w', encoding="utf-8") as f:
        f.write(str(text))
    return text


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: is_list_of_strings: Elapsed time: {:0.4f}'
)
def is_list_of_strings(lst: Any) -> bool:
    """Returns True if input is list of strings and false otherwise"""
    if lst and isinstance(lst, list):
        return all(isinstance(elem, str) for elem in lst)
    else:
        return False


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: read_text_file: Elapsed time: {:0.4f}'
)
def read_text_file(filename: Union[str, LocalPath], encoding: str = "utf-8-sig") -> str:
    """Read text from a file."""
    log.debug(f'START loading file {filename}')
    if not is_file(filename):
        raise FileNotFoundError(f'Text file "{filename}" not found.')

    content: str
    with io.open(filename, encoding=encoding) as f:
        content = str(f.read())
    log.debug(f'DONE loading of file {filename}')

    return content


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: load_pickle: Elapsed time: {:0.4f}'
)
def load_pickle(pickle_file: Union[str, LocalPath], access_mode: str = 'rb') -> Any:
    with open(pickle_file, access_mode) as f:
        return pickle.load(f)  # type:ignore


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: create_if_not_exists_containing_folder: Elapsed time: {:0.4f}'
)
def create_if_not_exists_containing_folder(file_path: Union[str, LocalPath]) -> None:
    """
    create containing folder if not exists
    Args:
        file_path:

    Returns:

    """
    Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: dump_pickle: Elapsed time: {:0.4f}'
)
def dump_pickle(obj: Any, pickle_file: Union[str, LocalPath], access_mode: str = 'wb') -> None:
    create_if_not_exists_containing_folder(file_path=pickle_file)
    with open(pickle_file, access_mode) as f:
        pickle.dump(obj, f)  # type:ignore


# TODO(jober) typing should be read_json_file(filename: str) -> Union[dict, list] !!!
@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: read_json_file: Elapsed time: {:0.4f}'
)
def read_json_file(filename: Union[str, LocalPath]) -> Any:
    """Read json from a file."""
    content: str = read_text_file(filename)
    try:
        log.debug(f'START JSON loading file {filename}')
        json_dict: Any = json.loads(content)
        log.debug(f'DONE JSON loading file {filename}')
        return json_dict
    except ValueError as e:
        raise ValueError(
            "Failed to read json from '{}'. Error: "
            "{}".format(os.path.abspath(filename), e)
        )


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: read_list_from_file: Elapsed time: {:0.4f}'
)
def read_list_from_file(filename: Union[str, LocalPath]) -> List[str]:
    """Read a list of strings from a file, line by line."""
    content = read_text_file(filename)
    try:
        str_list = content.splitlines(keepends=False)
        return str_list
    except ValueError as e:
        raise ValueError(
            "Failed to read a list of strings from '{}'. Error: "
            "{}".format(os.path.abspath(filename), e)
        )


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: read_csv_file: Elapsed time: {:0.4f}'
)
def read_csv_file(input_path: Union[str, LocalPath]) -> List[str]:
    """Reads a csv from a file"""
    result: List[str] = []
    with open(input_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter=',', quotechar='"')
        for row in csv_reader:
            result = result + row
    return result


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: dict_to_dataframe: Elapsed time: {:0.4f}'
)
def dict_to_dataframe(
    dictionary: Dict[Any, List[str]],
    last_entry: Any = None,
    sort_columns: bool = False
) -> pd.DataFrame:
    """Takes a dictionary with where each value is a list and returns a dataframe ready for export.
    It takes care to normalize the length of each value.
    If last_entry is provided, it is appended to each row"""
    _dictionary = dictionary.copy()

    if last_entry:
        for key in _dictionary:
            assert isinstance(_dictionary[key], list)
            _dictionary[key].append(last_entry)

    max_len = max(map(len, _dictionary.values()))

    # TODO(jober) gracefully handle non-string types
    # TODO(jober) add tests for string and non-string types
    default_item = ''
    for key in _dictionary:
        value_diff_len = _dictionary[key]
        assert isinstance(value_diff_len, list)

        value_same_len = value_diff_len + (max_len - len(value_diff_len)) * [default_item]

        _dictionary[key] = value_same_len

    df = pd.DataFrame.from_dict(_dictionary)

    if sort_columns:
        df = df.reindex(columns=sorted(df.columns))

    return df


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: write_dict_to_csv: Elapsed time: {:0.4f}'
)
def write_dict_to_csv(
    dictionary: Dict[Any, List[str]],
    output_path: Union[str, LocalPath],
    index: bool = False,
    last_entry: Any = None,
    sort_columns: bool = True
) -> None:
    """Takes a dictionary with where each value is a list and writes it to a csv from a file.
    It takes care to normalize the length of each value.
    If last_entry is provided, it is appended to each row"""
    df: pd.DataFrame = dict_to_dataframe(dictionary=dictionary, last_entry=last_entry, sort_columns=sort_columns)
    df.to_csv(output_path, index=index)


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: is_url: Elapsed time: {:0.4f}'
)
def is_url(resource_name: str) -> bool:
    """Return True if string is a http, ftp, or file URL path.
    This implementation is the same as the one used by matplotlib"""
    return URL_REGEX.match(resource_name) is not None


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: log_keep_max_num: Elapsed time: {:0.4f}'
)
def log_keep_max_num(log_path: Union[str, LocalPath]) -> None:
    """ Removes old logs"""
    if len(os.listdir(log_path)) > 10:
        # remove oldest file
        old_log = min(os.listdir(log_path), key=lambda f: os.path.getctime("{}/{}".format(log_path, f)))
        os.remove(log_path + '/' + old_log)


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: get_int_from_env: Elapsed time: {:0.4f}'
)
def get_int_from_env(env_variable_name: str, default_value: int = 0) -> int:
    int_str: str = os.getenv(env_variable_name, str(default_value)).strip()
    if int_str:
        try:
            int_value = int(int_str)
            return int_value
        except ValueError:
            return default_value
    else:
        return default_value


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: get_float_from_env: Elapsed time: {:0.4f}'
)
def get_float_from_env(env_variable_name: str, default_value: float = 0.0) -> float:
    float_str: str = os.getenv(env_variable_name, str(default_value)).strip()
    if float_str:
        try:
            float_value = float(float_str)
            return float_value
        except ValueError:
            return default_value
    else:
        return default_value


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: get_bool_from_env: Elapsed time: {:0.4f}'
)
def get_bool_from_env(env_variable_name: str, default_value: bool = False) -> bool:
    bool_value: bool = bool(str(os.getenv(env_variable_name, str(default_value))).lower() in ('true', '1', 't', 'True'))
    return bool_value


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: get_str_from_env: Elapsed time: {:0.4f}'
)
def get_str_from_env(env_variable_name: str, default_value: str = "") -> str:
    str_value: str = os.getenv(env_variable_name, default_value).strip()
    str_value = str_value.strip('\'"')  # Remove leading and trailing single or double quotes
    return str_value


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: get_context_and_decay_from_context_name: Elapsed time: {:0.4f}'
)
def get_context_and_decay_from_context_name(context_name: str) -> Tuple[str, Dict]:
    match: Optional[Match[str]] = re.search(r'([a-zA-Z-_]*)', context_name)
    if match:
        name_match: str = match.group(1)
    else:
        name_match = ''

    lifetime_match = re.search(r'\((\d*)\)', context_name)

    decay_interaction = int(4 if lifetime_match is None else lifetime_match.group(1))

    return name_match, {
        DECAY_FUNCTION_INTERACTION: decay_interaction,  # nr of interactions
        DECAY_FUNCTION_TIME: 150 * decay_interaction  # decay tim 2.5 min * decay
    }


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: safe_stringify: Elapsed time: {:0.4f}'
)
def safe_stringify(dubious_object: Union[str, dict]) -> str:
    """
    if the parameter is already a string, fine. if it is a dict, stringify the hell out of it
    Args:
        dubious_object: can be a string or a dict.

    Returns (str):

    """
    if isinstance(dubious_object, dict):
        return json.dumps(dubious_object)
    else:
        return dubious_object


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: find_key_in_nested_json: Elapsed time: {:0.4f}'
)
def find_key_in_nested_json(json_object: Union[List[Any], Dict[str, Any]], key: str) -> Any:
    """
    Find a key in a nested JSON object and return its corresponding value.

    Args:
        json_object (Union[List[Any], Dict[str, Any]]):
            A nested JSON object, which can be a dictionary or a list containing dictionaries.
        key (str):
            The key to search for in the JSON object.

    Returns:
        Any:
            The value corresponding to one of the occurrences of the specified key in the JSON object.
    """
    if isinstance(json_object, dict):
        for k, v in json_object.items():
            if k == key:
                return v
            if isinstance(v, (dict, list)):
                if find_key_in_nested_json(v, key):
                    return find_key_in_nested_json(v, key)
    elif isinstance(json_object, list):
        for d in json_object:
            if find_key_in_nested_json(d, key):
                return find_key_in_nested_json(d, key)
    return None


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: list_directories_in_directory: Elapsed time: {:0.4f}'
)
def list_directories_in_directory(path: str) -> List[str]:
    # Get a list of all entries (files and directories) in the directory
    entries: List[str] = os.listdir(path)

    # Filter out directories from the list and return only directory names
    directory_names: List[str] = [entry for entry in entries if os.path.isdir(os.path.join(path, entry))]

    return directory_names


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: list_files_in_directory_without_directories: Elapsed time: {:0.4f}'
)
def list_files_in_directory_without_directories(path: str) -> List[str]:
    # Get a list of all files in the directory
    files: List[str] = os.listdir(path)

    # Filter out directories from the list and return only file names
    file_names: List[str] = [file for file in files if os.path.isfile(os.path.join(path, file))]

    return file_names


@Timer(
    logger=log.debug, log_arguments=True,
    message='BPI helpers.py: clear_created_modified: Elapsed time: {:0.4f}'
)
def clear_created_modified(
    msg: Union[Message, str, int, float, bool, Enum, Struct],
) -> Union[Message, str, int, float, bool, Enum, Struct]:
    assert msg is not None, "msg object must not be None"

    if isinstance(msg, str) or isinstance(msg, int) or isinstance(msg, float) or isinstance(msg, bool):
        return msg

    if isinstance(msg, Struct) or isinstance(msg, Enum):
        return msg

    for field_descriptor in msg.DESCRIPTOR.fields:
        field_value: Any = getattr(msg, field_descriptor.name)

        # If this is a nested message, recursively process it
        if field_descriptor.type == field_descriptor.TYPE_MESSAGE:

            # Map
            if isinstance(field_value, MessageMap):
                for key, value in field_value.items():
                    if value is not None:
                        clear_created_modified(msg=value)

            # If it's a repeated field
            elif field_descriptor.label == field_descriptor.LABEL_REPEATED:
                for item in field_value:
                    if item is not None:
                        clear_created_modified(msg=item)
            else:
                # augment the created_at and modified_at Message fields
                if field_descriptor.name in CREATED_BY_MODIFIED_BY_CREATED_AT_MODIFIED_AT_SET:
                    if field_descriptor.name == 'created_at':
                        # augment these fields only if it is a create method
                        msg.ClearField("created_at")  # type:ignore
                    if field_descriptor.name == 'modified_at':
                        msg.ClearField("modified_at")  # type:ignore
                else:
                    if field_value is not None:
                        clear_created_modified(msg=field_value)
        else:

            # augment the created_by and modified_by fields
            if field_descriptor.name in CREATED_BY_MODIFIED_BY_CREATED_AT_MODIFIED_AT_SET:
                if field_descriptor.name == 'created_by':
                    msg.ClearField('created_by')

                if field_descriptor.name == 'modified_by':
                    msg.ClearField('modified_by')

    return msg
