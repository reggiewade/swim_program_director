from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
import state
import chatlib

# Load environment variables from .env file
load_dotenv()

# Load LLMs
macro_llm = chatlib.get_chat_model("BSU_").llm.with_structured_output(state.MacroCycle, method="json_mode")
meso_llm = chatlib.get_chat_model("BSU_").llm.with_structured_output(state.MesoCycle, method="json_mode")
micro_llm = chatlib.get_chat_model("BSU_").llm.with_structured_output(state.MicroCycle, method="json_mode")