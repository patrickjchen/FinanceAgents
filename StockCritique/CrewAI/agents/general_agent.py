import openai
from dotenv import load_dotenv
import os
from agents.monitor import MonitorAgent
from datetime import datetime
import traceback
import json
import random
from mcp.schemas import MCPRequest, MCPResponse

# Load environment variables
load_dotenv()  # Loads from .env file

class GeneralAgent:
    def __init__(self):
        self.monitor = MonitorAgent()
        self.api_key = os.getenv("OPENAI_API_KEY")  # Read from .env
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        self.client = openai.OpenAI(api_key=self.api_key)
        self.prompts = [
            "As a professional documentary writer, answer the following question in a friendly and informative tone:",
            "As a scientist, provide a clear and friendly explanation to the following question:",
            "Imagine you are writing a popular science article. Please answer the following question in a way that's both accurate and approachable:",
            "As a science communicator, respond to the following question with clarity and warmth:",
            "As a documentary narrator, answer this question in a way that is both engaging and easy to understand:",
            # Few-shot style prompts:
            "Reader: Can you explain this concept simply?\nWriter: Absolutely! Here is a simple explanation... Now, answer the following question:",
            "Student: Why does this happen?\nScientist: Great question! Let me explain... Now, answer the following question:",
            "Audience: What is the significance of this discovery?\nNarrator: This discovery is important because... Now, answer the following question:",
            "Curious Mind: How does this work?\nScience Writer: Let me break it down for you... Now, answer the following question:"
        ]

    def run(self, request: MCPRequest) -> MCPResponse:
        start_time = datetime.now()
        status = "processing"
        try:
            user_query = request.context.user_query
            prompt = random.choice(self.prompts)
            print(f"[GeneralAgent] Received query at {start_time}: {user_query}")
            self.monitor.log_health("GeneralAgent", "Received query", f"Timestamp: {start_time}, Query: {user_query}")
            full_prompt = f"{prompt} {user_query}"
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": full_prompt}]
            )
            answer = response.choices[0].message.content
            # Output as a long text string, not JSON
            formatted_answer = (
                f"GeneralAgent Response\n"
                f"Question: {user_query}\n\n"
                f"{answer}"
            )
            status = "success"
        except Exception as e:
            formatted_answer = str(e)
            status = "failed"
        completed_time = datetime.now()
        log_message = {
            "agent": "GeneralAgent",
            "started_timestamp": start_time.isoformat(),
            "response": formatted_answer,
            "completed_timestamp": completed_time.isoformat(),
            "status": status
        }
        try:
            with open("monitor_logs.json", "a") as f:
                f.write(json.dumps(log_message) + "\n")
        except Exception as e:
            print(f"[GeneralAgent] Logging error: {e}")
        return MCPResponse(
            request_id=request.request_id,
            data={"general": formatted_answer},
            context_updates=None,
            status=status
        )

    def _log(self, message: dict):
        with open('monitor_logs.json', 'a') as f:
            f.write(json.dumps(message) + '\n')
        print(json.dumps(message, indent=2))