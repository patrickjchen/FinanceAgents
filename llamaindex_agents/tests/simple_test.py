from openai import OpenAI
client = OpenAI()  # reads OPENAI_API_KEY (and optional OPENAI_ORG / OPENAI_PROJECT)
r = client.responses.create(model="gpt-4o-mini", input="say 'ok' once")
print(r.output_text)

