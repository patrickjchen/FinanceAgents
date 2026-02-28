import os
import asyncio
import openai

AGENT_TIPS = {
    "reddit": "Reddit agent response is related to stock market topics on social media with sentiment analysis.",
    "finance": "Finance agent response is about company's info from internal financial docs.",
    "yahoo": "Yahoo agent response is about statistic data and summary based on real time stock price per company in last 30 days.",
    "sec": "SEC agent response is about public company's financial info from SEC files."
}


async def improve_agent_response(agent: str, content: str, agent_tips: dict = None) -> str:
    """Use LLM to improve, summarize, and clean up agent output."""
    if not content:
        return ""
    tips = agent_tips or AGENT_TIPS
    tip = tips.get(agent, "")
    prompt = (
        f"You are an expert assistant. Here is a response from the {agent} agent. "
        f"{tip}\n"
        f"Please improve the output format, summarize the response, and remove unrelated content. "
        f"Your summary must include key data and important content from the agent's response (not just file names), so the user gets all relevant information. "
        f"Make the summary informative and retain important details, not just a list of file names. "
        f"Include the agent name in the summary.\n\nResponse:\n{content}"
    )
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return content  # fallback
        client = openai.OpenAI(api_key=api_key)
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
        )
        return response.choices[0].message.content
    except Exception as e:
        with open("monitor_logs.json", "a") as f:
            f.write(f"LLM error for {agent}: {e}\n")
        return content


async def generate_comprehensive_summary(user_query: str, agent_results: dict) -> str:
    """Generate a comprehensive summary combining all agent outputs."""
    if not agent_results:
        return ""
    combined = "\n\n".join(
        f"--- {name} ---\n{data.get('summary', str(data))}"
        for name, data in agent_results.items()
    )
    prompt = (
        f"You are a senior financial analyst. The user asked: \"{user_query}\"\n\n"
        f"Below are the analysis results from multiple specialized agents:\n\n"
        f"{combined}\n\n"
        f"Please provide a comprehensive summary that:\n"
        f"1. Synthesizes key findings from all agents\n"
        f"2. Highlights important financial metrics, stock data, and sentiment\n"
        f"3. Provides an overall assessment of the company/stock\n"
        f"4. Notes any risks or concerns\n"
        f"Keep the summary concise but informative."
    )
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Summary unavailable (no API key)."
        client = openai.OpenAI(api_key=api_key)
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        )
        return response.choices[0].message.content
    except Exception as e:
        with open("monitor_logs.json", "a") as f:
            f.write(f"LLM error for summary: {e}\n")
        return "Summary generation failed."
