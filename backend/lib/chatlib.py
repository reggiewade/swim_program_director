#****************************************************************************
# chatlib.py - Chat model support files
# v4
# Boise State University CS 497
# Dr. Henderson
# Spring 2026
#
# Wraps the langchain llm class to include support for the Boise State AI API
# and other features.
#
# Use get_chat_model() to get a model. Values must be set in a .env file:
# MODEL_PROVIDER : the name of the provider, e.g. openai, or boise-state
# MODEL_CHAT : must be a supported model from the provider
# PROVIDER_URL : if a custom url is used set it here
# API_KEY : the secret api key for the model provider
#
# You can pass a prefix like get_chat_model('BSU_') and it will load
# the corresponding environment variables, e.g. BSU_API_KEY. This allows
# you to load multiple models from different providers.
#
# Use the returned objects to call the chat() method passing in the
# messages and config dict, or access the model directly with the llm field
#----------------------------------------------------------------------------
from dotenv import load_dotenv
from typing import List, Optional
import requests
import os

from langchain.chat_models.base import BaseChatModel
from langchain_core.tools import BaseTool
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage, convert_to_openai_messages
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_aws import ChatBedrockConverse
from pydantic import PrivateAttr

load_dotenv()

class BoiseStateChatModel(BaseChatModel):
    model_id: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    base_url: str = "https://api.boisestate.ai/chat/api-converse"

    _bedrock: ChatBedrockConverse = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._bedrock = ChatBedrockConverse(
            model_id=self.model_id,
            region_name="us-west-1"
        )

    def bind_tools(self, tools: List[BaseTool], **kwargs):
        return self.model_copy(update={"bound_tools": tools})
    
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs):
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        #payload = self._bedrock._format_params(messages=messages)
        payload = {
            'modelId': self.model_id,
        }
        bedrock_msgs = []
        system_blocks = []

        for m in messages:
            if isinstance(m, SystemMessage):
                system_blocks.append({"text": m.content})
            elif isinstance(m, HumanMessage):
                bedrock_msgs.append({"role": "user", "content": [{"text": m.content}]})
            elif isinstance(m, AIMessage):
                bedrock_msgs.append({"role": "assistant", "content": [{"text": m.content}]})

        payload["system"] = system_blocks
        payload["messages"] = bedrock_msgs

        for param, bsu_param in (('temperature', 'temperature'), ('max_tokens', 'maxTokens'), ('top_p', 'topP')):
            if  param in kwargs:
                payload[bsu_param] = kwargs[param]

        #print(headers)
        #print(payload)
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        data = response.json()

        #print(data)

        if "error" in data:
            message = AIMessage(content=data['message'])
        elif "text" in data:
            message = AIMessage(content=data['text'])    
        else:
            message = AIMessage(content="Unknown error")
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    
    @property
    def _llm_type(self):
        return "boise-state"

class ChatModel:

    def __init__(self, llm):
        self.llm = llm

    def bind_tools(self, tools: List[BaseTool]):
        self.llm = self.llm.bind_tools(tools)

    def invoke(self, messages, options=None, **kwargs):
        # Preserve compatibility with agent code that calls llm.invoke(...)
        # and normalize any 'options' payload into the config dict.
        if options is not None:
            kwargs.update(options)
        return self.chat(messages, config=kwargs)

    def chat(self, messages, config={}):
        #print(f"CONFIG: {config}, llm-type: {self.llm._llm_type}")
        kwargs = { **config }
        if self.llm._llm_type == 'chat-ollama':
            if 'max_tokens' in kwargs:
                kwargs['num_predict'] = config['max_tokens']
                del kwargs['max_tokens']
            response = self.llm.invoke(messages, options=kwargs)
        else:
            #if 'max_tokens' in kwargs:
            #    kwargs['max_completion_tokens'] = config['max_tokens']
            #    del kwargs['max_tokens']
            response = self.llm.invoke(messages, **kwargs)

        #print(f"{type(response)}: {response}")

        for key in [ 'temperature', 'top_p', 'max_tokens' ]:
            if key in config: response.additional_kwargs[key] = config[key]

        #print("Setting tokens")
        tokens = response.usage_metadata
        if tokens:
            #messages[-1].response_metadata['token_usage'] = { 'prompt_tokens': tokens.get('input_tokens') }
        #else:
            meta = response.response_metadata
            tokens = meta.get('token_usage')
            if tokens:
                messages[-1].response_metadata['token_usage'] = { 'prompt_tokens': tokens.get('prompt_tokens') }

        return response

def get_chat_model(env_prefix=""):
    model = os.getenv(f"{env_prefix}MODEL_CHAT")
    key = os.getenv(f"{env_prefix}API_KEY")
    provider = os.getenv(f"{env_prefix}MODEL_PROVIDER")
    print(f"Using {provider} with model {model}")

    assert model, f"{env_prefix}MODEL_CHAT not defined in environment"
    assert key, f"{env_prefix}API_KEY not defined in environment"
    assert provider, f"{env_prefix}MODEL_PROVIDER not defined in environment"

    if os.getenv(f"{env_prefix}MODEL_PROVIDER") == "boise-state":
        llm = BoiseStateChatModel(model_id = model, api_key=key)
    else:
        llm = init_chat_model(
            model,
            configurable_fields=["temperature", "top_p", "max_tokens" ],
            model_provider=provider,
            base_url=os.getenv(f'{env_prefix}PROVIDER_URL'),
            api_key=key
        )

    return ChatModel(llm)
    
