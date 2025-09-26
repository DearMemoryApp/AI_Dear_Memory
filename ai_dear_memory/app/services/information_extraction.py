from app.prompts.info_extraction import EXTRACTION_PROMPT
from app.services.chain_creation import create_chain


async def extract_key_value_pairs(input_text: str) -> dict:
    try:
        result = await create_chain(EXTRACTION_PROMPT, {"input_text": input_text})
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}
