import os
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers.json import SimpleJsonOutputParser
from app.core.config import settings

os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", temperature=0, max_tokens=None, timeout=None, max_retries=2
)


async def create_chain(prompt_template, input_data):
    try:
        prompt = ChatPromptTemplate.from_messages(prompt_template)
        json_parser = SimpleJsonOutputParser()
        chain = prompt | llm | json_parser
        result = await asyncio.to_thread(chain.invoke, input_data)
        return result
    except Exception as e:
        print(f"An error occurred during chain execution: {e}")
        return {}
