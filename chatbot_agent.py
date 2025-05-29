import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.utils.function_calling import convert_to_openai_function

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from booking_system import check_availability, book_appointment, get_all_services

class ChatbotAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = self._initialize_tools()
        self.agent_executor = self._initialize_agent()

    def _initialize_llm(self):
        """Initialize with creative but controlled parameters"""
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",  # More advanced model
            temperature=0.8,  # Higher creativity
            top_p=0.9,  # For more diverse responses
            convert_system_message_to_human=True
        )

    def _safe_check_availability(self, args: Dict[str, Any]) -> list:
        """Wrapper for check_availability with error handling"""
        try:
            return check_availability(args["service_type"], args["date"])
        except Exception as e:
            logger.error(f"CheckAvailability error: {e}")
            return []

    def _safe_book_appointment(self, args: Dict[str, Any]) -> bool:
        """Wrapper for book_appointment with error handling"""
        try:
            return book_appointment(
                args["service_type"],
                args["date"],
                args["time"],
                args["user_name"]
            )
        except Exception as e:
            logger.error(f"BookAppointment error: {e}")
            return False

    def _initialize_tools(self):
        """Enhanced tool descriptions for better AI understanding"""
        return [
            Tool(
                name="CheckAvailability",
                func=self._safe_check_availability,
                description="Check available slots. Parameters: {'service_type': string, 'date': 'YYYY-MM-DD'}. Returns list of times."
            ),
            Tool(
                name="BookAppointment",
                func=self._safe_book_appointment,
                description="Finalize booking. Parameters: {'service_type': string, 'date': 'YYYY-MM-DD', 'time': 'HH:MM', 'user_name': string}. Returns boolean."
            ),
            Tool(
                name="ListServices",
                func=lambda _: get_all_services(),
                description="Get all offered services. No parameters needed. Returns service names and descriptions."
            )
        ]

    def _create_prompt(self):
        """More nuanced system prompt guiding natural conversation"""
        return ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a highly skilled booking assistant with exceptional conversational abilities. Your responses must:

1. Flow naturally like human conversation with varied phrasing
2. Never use repetitive or robotic language
3. Handle misunderstandings gracefully by asking thoughtful follow-ups
4. Adapt responses based on conversation history
5. For unrecognized requests, creatively connect to bookable services
6. Maintain professional yet warm tone with natural empathy

Current services are in-person only. When users ask about unavailable services like virtual meetings:
- Acknowledge naturally
- Highlight benefits of in-person services
- Suggest alternatives without being pushy"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

    def _initialize_agent(self):
        """Configure agent for maximum conversational ability"""
        prompt = self._create_prompt()
        functions = [convert_to_openai_function(tool) for tool in self.tools]
        llm_with_tools = self.llm.bind(functions=functions)
        
        agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors="Check your input and try again",  # Let LLM handle errors
            max_iterations=6  # Allow more reasoning steps
        )

    def get_response(self, user_input: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Let the AI handle all responses naturally"""
        try:
            lc_messages = []
            if chat_history:
                for msg in chat_history:
                    if msg["sender"] == "user":
                        lc_messages.append(HumanMessage(content=msg["message"]))
                    else:
                        lc_messages.append(AIMessage(content=msg["message"]))
            
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": lc_messages,
            })
            
            return result["output"]
        
        except Exception as e:
            logger.error(f"Conversation error: {e}")
            # Let the LLM generate even error responses
            recovery_response = self.llm.invoke(
                f"The user said: '{user_input}'\n"
                "Our booking system encountered a technical hiccup. "
                "Craft a polite, natural response that:\n"
                "1. Acknowledges the issue\n"
                "2. Keeps the conversation flowing\n"
                "3. Suggests rephrasing or alternative actions\n"
                "Respond like a professional human assistant:"
            )
            return recovery_response.content

# Singleton instance
chatbot_agent = ChatbotAgent()

def get_chatbot_response(user_input: str, chat_history: List[Dict[str, str]] = None) -> str:
    return chatbot_agent.get_response(user_input, chat_history)