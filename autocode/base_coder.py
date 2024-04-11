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

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Dict,
    List,
    Optional,
)


@dataclass
class FunctionCoder:
    """
    class to generate a run-able python function string from the provided parameters
    type hints are included need to be provided
    !the output is not checked for python-interpretability!

    example indent_lvl=0:
    >> def my_function():
    >> [4x" "]pass

    example indent_lvl=1:
    >> class SomeClass:  # some other class, into which the "autocoded" class is nested
    >> [4x" "]def my_function():
    >> [4x" "][4x" "]pass

    Attributes:
        indent_lvl: indent level of the 'def' statement of the function, 1 -> 4 spaces, 2 -> 8 spaces, etc.
        arguments: arguments of the function, dict: argument_name -> argument_type
        returns: return names and types of functions
        add_lines: additional lines to add between def xxx() and return xxx
        docstring: lines of docstring to add to the function
    """

    indent_lvl: int  # indent level of 'def', 0 => indent_str="", 1 => indent_str=4x" ", 2 => indent_str=8x" ", etc.
    arguments: Dict[str, str]  # arg_name : arg_type
    function_name: str  # name of function, arguments will be passed to it, output will be returned
    returns: Dict[str, str]  # return_name: return_type
    add_lines: Optional[List[str]] = None  # add lines instead of function call
    docstring: List[str] = field(default_factory=lambda: [""])
    _repr: str = ""
    _std_indent: str = "    "
    _indent_str: str = ""
    _args_inp: str = ""
    _args_fct: str = ""
    _function_to_call: str = ""
    _add_lines: str = ""
    _return_type: str = ""
    _return_of_fct: str = ""
    _return_statement: str = ""
    _docstring: str = '"""[PLACEHOLDER]"""'
    _built: bool = False

    def build_indent_string(self) -> None:
        for i in range(0, self.indent_lvl):
            self._indent_str += self._std_indent

    def build_arguments_input_string(self) -> None:
        for arg_name, arg_type in self.arguments.items():
            if arg_name == "self":
                self._args_inp += f"{arg_name}, "
            else:
                self._args_inp += f"{arg_name}: {arg_type}, "
        if len(self._args_inp) > 0:
            self._args_inp = self._args_inp[:-2]

        # clean up double commas
        self._args_inp = self._args_inp.replace(",,", ",")

    def build_argument_fct_string(self) -> None:
        for arg_name, _ in self.arguments.items():
            if arg_name == "self":
                continue
            self._args_fct += f"{arg_name}={arg_name}, "
        if len(self.arguments) > 0:
            self._args_fct = self._args_fct[:-2]

    def build_return_type(self) -> None:
        for _, return_type in self.returns.items():
            self._return_type += return_type + ", "
        if len(self._return_type) > 0:
            self._return_type = f"{self._return_type[:-2]}"
        if len(self.returns) > 0:
            if len(self.returns) == 1:
                self._return_type = f" -> {self._return_type}"
            else:
                self._return_type = f" -> Tuple[{self._return_type}]"

    def build_return(self) -> None:
        if len(self.returns) > 0:
            for return_name, return_type in self.returns.items():
                # if "Empty" in return_type:
                #     return
                self._return_statement += f"{return_name}, "
            self._return_of_fct = f"{self._return_statement[:-2]} = "
            self._return_statement = f"{self._std_indent}{self._indent_str}return {self._return_statement[:-2]}\n"

    def build_docstring(self) -> None:
        docstring_lines = ""
        for docs in self.docstring:
            docstring_lines += f"{self._std_indent}{self._indent_str}{docs}\n"

        self._docstring = (
            f'{self._std_indent}{self._indent_str}"""\n'
            + f"{docstring_lines}"
            + f'{self._std_indent}{self._indent_str}"""\n'
        )

    def build_additional_lines(self) -> None:
        if self.add_lines:
            for line in self.add_lines:
                self._add_lines += f"{self._std_indent}{self._indent_str}{line}\n"

    def build_code_string(self) -> None:
        self.build_indent_string()
        self.build_docstring()
        self.build_arguments_input_string()
        self.build_argument_fct_string()
        self.build_return_type()
        self.build_return()
        self.build_additional_lines()
        self._repr = (
            ""
            + f"{self._indent_str}def {self.function_name}({self._args_inp}){self._return_type}:\n"
            + f"{self._docstring}"
            + f"{self._add_lines}"
            + f"{self._return_statement}"
            + ""
        )
        self._built = True

    def get_code_string(self) -> str:
        if not self._built:
            self.build_code_string()

        return self._repr


@dataclass
class ClassCoder:
    """
    class to generate a run-able class string from the provided parameters
    type hints are included need to be provided
    does not include import statements
    !the output is not checked for runability!

    example indent_lvl=0:
    >> class MyClass():
    >> [4x" "]pass

    example indent_lvl=1:
    >> class OtherClass:  # some other class, into which the "autocoded" class is nested
    >> [4x" "]def MyClass():
    >> [4x" "][4x" "]pass

    Attributes:
        name: name of the class
        docstring: docstring to include in the class
        inits: lines of code to include right after class initialization statement ('class xxx')
        indent_lvl: indent level of the 'class' statement of the function, 1 -> 4 spaces, 2 -> 8 spaces, etc.
        functions: class-functions, need to have correct indent_lvl
        base_class: optional base class of generated class
    """

    name: str
    docstring: List[str]
    inits: List[str]
    indent_lvl: int  # indent level of 'class', 0 => indent_str="", 1 => indent_str=4x" ", 2 => indent_str=8x" ", etc.
    functions: List[FunctionCoder]
    base_class: str = ""
    _indent_str: str = ""
    _name_str: str = ""
    _std_indent: str = "    "  # 4x" "
    _init_str: str = ""
    _functions_str: str = ""
    _docstring: str = ""
    _repr: str = ""
    _built: bool = False

    def build_indent_string(self) -> None:
        for i in range(0, self.indent_lvl):
            self._indent_str += self._std_indent

    def build_docstring(self) -> None:
        docstring_lines = ""
        for docs in self.docstring:
            docstring_lines += f"{self._std_indent}{self._indent_str}{docs}\n"

        self._docstring = (
            f'{self._std_indent}{self._indent_str}"""\n'
            + f"{docstring_lines}"
            + f'{self._std_indent}{self._indent_str}"""\n'
        )

    def build_init_string(self) -> None:
        for init in self.inits:
            self._init_str += f"{self._std_indent}{self._indent_str}{init}\n"

    def build_name_string(self) -> None:
        if self.base_class != "":
            self._name_str = f"class {self.name}({self.base_class}):\n"
        else:
            self._name_str = f"class {self.name}:\n"

    def build_functions_string(self) -> None:
        for function in self.functions:
            code = function.get_code_string()
            self._functions_str += "\n" + f"{code}"

    def build_code_string(self) -> None:
        self.build_indent_string()
        self.build_name_string()
        self.build_docstring()
        self.build_init_string()
        self.build_functions_string()
        self._repr = (
            f"{self._indent_str}{self._name_str}"
            + f"{self._docstring}"
            + f"{self._init_str}"
            + f"{self._functions_str}"
            + ""
        )
        self._built = True

    def get_code_string(self) -> str:
        if not self._built:
            self.build_code_string()
        return self._repr
