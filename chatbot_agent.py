import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
import random

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
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
        self.conversation_state = {}

    def _initialize_llm(self):
        if not os.getenv("GOOGLE_API_KEY"):
            logger.warning("GOOGLE_API_KEY not found in .env")
        
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            temperature=0.7,  # Increased for more varied responses
            convert_system_message_to_human=True
        )

    def _initialize_tools(self):
        return [
            Tool(
                name="CheckAvailability",
                func=self._safe_check_availability,
                description="Check available slots for a service. Input: {'service_type': str, 'date': 'YYYY-MM-DD'}"
            ),
            Tool(
                name="BookAppointment",
                func=self._safe_book_appointment,
                description="Book an appointment. Input: {'service_type': str, 'date': 'YYYY-MM-DD', 'time': 'HH:MM', 'user_name': str}"
            ),
            Tool(
                name="GetAllServices",
                func=lambda _: get_all_services(),
                description="List all available services. Input: {}"
            )
        ]

    def _create_prompt(self):
        return ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a friendly, human-like appointment booking assistant. Follow these guidelines:
1. Be conversational and natural - use casual language and occasional pleasantries
2. When asking for information, be polite and explain why you need it
3. Vary your responses - don't repeat the same phrases
4. Show empathy and understanding
5. Use natural transitions between topics
6. Confirm details before booking
7. If the user asks the same question twice, provide a slightly different response
8. Maintain a helpful, professional but friendly tone"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

    def _initialize_agent(self):
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
            handle_parsing_errors=True,
            max_iterations=5
        )

    def _safe_check_availability(self, args: Dict[str, Any]) -> list:
        try:
            return check_availability(args["service_type"], args["date"])
        except Exception as e:
            logger.error(f"CheckAvailability error: {e}")
            return []

    def _safe_book_appointment(self, args: Dict[str, Any]) -> bool:
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

    def get_response(self, user_input: str, chat_history: List[Dict[str, str]] = None) -> str:
        try:
            lc_messages = []
            if chat_history:
                for msg in chat_history:
                    if msg["sender"] == "user":
                        lc_messages.append(HumanMessage(content=msg["message"]))
                    else:
                        lc_messages.append(AIMessage(content=msg["message"]))
            
            # Add some randomness to make responses more natural
            if random.random() < 0.3:  # 30% chance to add a small delay
                pass  # Could add artificial delay here if desired

            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": lc_messages,
            })
            
            return self._humanize_response(result["output"])
        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            return random.choice([
                "Hmm, I'm having trouble with that. Could you try again?",
                "Sorry, I didn't catch that. Mind rephrasing?",
                "I'm having a bit of trouble. Let's try that again."
            ])

    def _humanize_response(self, response: str) -> str:
        """Add natural language variations to responses"""
        greetings = ["Hi there!", "Hello!", "Hey!", ""]
        closings = ["", "Let me know if you need anything else!", "How can I help further?", "What else can I do for you?"]
        
        if random.random() < 0.4:  # 40% chance to add greeting
            response = f"{random.choice(greetings)} {response}"
        if random.random() < 0.3:  # 30% chance to add closing
            response = f"{response} {random.choice(closings)}"
        
        return response.strip()

chatbot_agent = ChatbotAgent()

def get_chatbot_response(user_input: str, chat_history: List[Dict[str, str]] = None) -> str:
    return chatbot_agent.get_response(user_input, chat_history)