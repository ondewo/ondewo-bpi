# Release History

*****************

## Release ONDEWO BPI v4.1.1

### Bug Fixes

* QA Response. The original QA response is no longer overridden by the QA response to track in the CAI.

*****************

## Release ONDEWO BPI v4.1.0

### Improvements

* Extend the Q&A BPI version to support filtering functionality through context injection

The Q&A URL filter can be leveraged to control which resources can Q&A look into for answers.
The resources are identified by their URLs, therefore, the filters are regexes applied to the URLS.

See below and example of a 'c-qa-url-filter' injection:

```json
{
  "name": "projects/11111111-1111-1111-1111-111111111111/agent/sessions/00000000-0000-4000-8000-decaf0cafe06/c-qa-url-filter",
  "lifespan_count": "100000",
  "parameters": {
    "base-filter": {
      "display_name": "base-filter",
      "value": ".*/my_base_filter/.*"
    },
    "provisional-filter": {
      "display_name": "provisional-filter",
      "value": ".*/my_provisional_filter/.*"
    }
  }
}
```

> The *base filter* defines the base behaviour of the filter.
>
> The *provisional filter* will override the *base filter* if defined.
>
> If filter context parameters are specified, or no 'c-qa-url-filter' is specified, the filter applied will be `.*` (default behaviour == no filter).

### Bug Fixes

* Correct mis-usage of logging levels

*****************

## Release ONDEWO BPI v4.0.1

### Bug Fixes
* Improvements on the example usage of the `IntentMaxTriggerHandler`

*****************

## Release ONDEWO BPI v4.0.0

### Improvements

* All the handlers now have the client as an input too in case it's needed
* Add intent counter handler so you can register an intent or more with a maximum number of occurrences then it triggers a 'Default Exit Intent'

You need to modify this dictionary in the intent_max_trigger_handler as you wish
```python
intent_with_max_number_triggers_dict = {'Default Fallback Intent': 2, 'intent-A': 3}
```
Then in your BPI you can use the handler function right away and register handlers with this Callable
```python
    def register_handlers(self) -> None:
        self.register_intent_handler(
            intent_pattern="intent-A", handlers=[IntentMaxTriggerHandler.handle_if_intent_reached_number_triggers_max]
        )
```

*****************

## Release ONDEWO BPI v3.0.1

### Improvements
* Add configurable "truncation" limit for long input sentences 

*****************
## Release ONDEWO BPI v3.0.0
### Improvements 
* Enable the configuration of the CentralClientProvider to be passed (optionally)
* Support of patterns to invoke intent callbacks

### Bug Fixes
* Dynamic login enabled

### Breaking Changes
This version holds small renaming and typing changes on the BPI Server:
  * `self.intent_handlers` is now a `List[IntentCallbackAssignor]` instead of a dictionary; custom code in the `register_handlers` function will need adaptation. 
  * The `intent_name` field of the `registered handlers` now supports patterns, therefore its name changed to `intent_pattern`.
  * The `handler` field of the `registered handlers` now contains a list of callables, therefore was renamed to `handlers`.

Below an example of how it should look after the update:

```python
    def register_handlers(self) -> None:
        self.register_intent_handler(
            intent_pattern=r"i.my_\.*", handlers=[self.reformat_text_in_intent],
        )
        self.register_intent_handler(
            intent_pattern="i.my_handled_intent", handlers=[self.reformat_text_in_intent],
        )
```

*****************
## Release ONDEWO BPI v2.0.4
### New Features
* Support NLU API 2.0.x

### Improvements
* Support streaming connections

*****************
## Release ONDEWO BPI v2.0.3
### New Features

* upload to pypi

*****************
## Release ONDEWO BPI v2.0.2
### Bug Fixes

* imrpoved log output for debugging
* updated to use ondewo-logging pip repo

*****************
## Release ONDEWO BPI v2.0.1
### Bug Fixes

* updated README
* updated sip example import path

*****************

## Release ONDEWO BPI v2.0.0
### New Features

* refactored
* updated all submodules and clients
* moved to github

### Improvements

* added examples, refactored the servers so they are consistent and more clear

### Breaking Changes

* the code for generating contexts has changed:
* * this version (currently compatible with the develop version of CAI):
```python
def create_parameter_dict(my_dict: Dict) -> Optional[Dict[str, context_pb2.Context.Parameter]]:
    assert isinstance(my_dict, dict) or my_dict is None, "parameter must be a dict or None"
    if my_dict is not None:
        return {
            key: context_pb2.Context.Parameter(
                display_name=key,
                value=my_dict[key]
            )
            for key in my_dict
        }
    return None
```
* * old version (compatible with the current production CAI):

```python
from google.protobuf.struct_pb2 import Struct


def get_protobuf_struct_from_dict(my_dict: Dict) -> Struct:
    assert isinstance(my_dict, dict) or my_dict is None, "parameter must be a dict or None"
    result: Struct = Struct()
    if my_dict is not None:
        for key, value in my_dict.items():
            result[key] = value
    return result
```

### Known issues not covered in this release

* sip-client-python not open source, therefore it needs to be added seperately for external customers to use it

### Migration Guide

* change your upstreams to github

*****************
## Release ONDEWO RELEASE Template
### New Features
### Improvements
### Bug fixes
### Breaking Changes
### Known issues not covered in this release
### Migration Guide

*****************
