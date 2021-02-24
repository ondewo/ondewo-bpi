![Logo](https://raw.githubusercontent.com/ondewo/ondewo-logos/master/github/ondewo_logo_github_2.png)

# Ondewo Bpi

## The BPI (Business Process Integration) Module

This module sits between the user and CAI:
```
          _______           _______
         |       |         |       |
==grpc==>|  BPI  |==grpc==>|  CAI  |
<==grpc==|       |<==grpc==|       |
         |_______|         |_______|
```
and has full access to the outgoing request and the response. It also known the location of CAI and has authorization, meaning it can edit the state of CAI directly with additional informaion.


A simple example of a server using the BPI looks like this:
```python
import logging

from ondewo.nlu import session_pb2
from ondewo_bpi.bpi_server import BpiServer
import ondewo_bpi.helpers as helpers


class MyServer(BpiServer):
    def __init__(self) -> None:
        super().__init__()                        # initialize the server (parent class)
        self.register_handlers()                  # add handlerss for intents

    def register_handlers(self) -> None:          # the mapping from handled intents to functions
        self.register_handler(
            intent_name='i.my_handled_intent',    # a user-created intent
            handler=self.reformat_text_in_intent, # the function to handle it
        )
        self.register_handler(
            intent_name='Default Fallback Intent',  # a default (system created) intent
            handler=self.handle_default_fallback,   # the function to handle it
        )

    def reformat_text_in_intent(      # the handler functions take responses in an out, and can process parts of the response
        self, response: session_pb2.DetectIntentResponse
    ) -> session_pb2.DetectIntentResponse:
        return helpers.replace_text_in_response(
            search="<REPLACE:REPLACE_THIS_TEXT>",   # this entire pseudo-command would go in a text response for example
            replace="new text",
            response=response
        )

    def handle_default_fallback(      # the handler functions can also just trigger events and leave the response unchanged
        self, response: session_pb2.DetectIntentResponse
    ) -> session_pb2.DetectIntentResponse:
        logging.warning("Default fallback was triggered!")
        return response
```
There is a more complete example in ondewo_bpi.example.py which is hooked up to run via the Dockerfile (just do `docker-compose up -d && docker-compose logs -f`).

Have a look at the docker-compose file, and the sample.env. The port that the bpi listens on functionally replaces the cai port, so at the frontend you just have to point to a different port to use the bpi, there is no other difference. And the cai port will still be available as well, so switching between using CAI directly and using the BPI is just a matter of changing a single variable, the port.

|CAI|BPI|
|---|---|
|HOST=localhost:50055|HOST=localhost:50051|
