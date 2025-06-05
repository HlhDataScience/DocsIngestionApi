from openai import AsyncAzureOpenAI, OpenAIError, AsyncOpenAI
from typing import Dict, Generator, Tuple
from itertools import tee
import asyncio
import json
import logging

def setup_credentials(api_key: str, api_version: str, endpoint: str, deployment: str) ->Dict[str, str]:
    return {
        "api_key": api_key,
        "api_version": api_version,
        "endpoint": endpoint,
        "deployment": deployment,
    }

def setup_openai_client(api_key: str, api_version: str, endpoint: str, deployment: str)->AsyncOpenAI:

    credentials = setup_credentials(api_key, api_version, endpoint, deployment)

    try:
        client = AsyncAzureOpenAI(
            api_key=credentials["api_key"],
            api_version=credentials["api_version"],
            azure_endpoint=credentials["endpoint"],
            azure_deployment=credentials["deployment"],
        )
        return client

    except ValueError as ve:
        raise ValueError(f"Invalid parameter in OpenAI client initialization: {ve}")
    except OpenAIError as oe:
        raise OpenAIError(f"OpenAI SDK error during client init: {oe}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during client initialization: {e}")


async def generate(
api_key: str, api_version: str, endpoint: str, deployment: str,
        prompt: str,
        original_doc: Tuple[str, str],
        prompt_type: str,
    ) -> str:
        try:
            if prompt_type == "To_document":
                formatted_prompt = (
                    f"{prompt}\nDOCUMENT\n"
                    f"Question: {original_doc[0]}\n"
                    f"Answer: {original_doc[1]}"
                )
            else:
                formatted_prompt = (
                    f"{prompt}\nQuestion&Answer\n"
                    f"Title: {original_doc[0]}\n"
                    f"Paragraph: {original_doc[1]}"
                )

            client = setup_openai_client(api_key, api_version, endpoint, deployment)
            response = await client.chat.completions.create(
                model="ubot-dev-gpt4omin",
                temperature=0.0,
                messages=[
                    {"role": "system", "content": formatted_prompt}
                ],
            )

            return response.choices[0].message.content

        except OpenAIError as oe:
            raise RuntimeError(f"OpenAI API error during generation: {oe}")
        except ValueError as ve:
            raise ValueError(f"Invalid input to generate method: {ve}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during prompt generation: {e}")



async def doc_to_qa(prompt:str, docs: Generator[Tuple[str, str], None, None],
                    output_file: str
                    ) -> None:
    task_list = []
    docs_for_len_0, docs_for_len_1, docs = tee(docs, 3)
    logging.info(f"the length of the docs is {sum(1 for _ in docs_for_len_0)}")
    for i, doc in enumerate(docs):
        task = asyncio.create_task(generate(
            prompt=prompt,
            original_doc=doc,
            prompt_type="to_qa"))
        task_list.append(task)

    results = await asyncio.gather(*task_list)
    all_results = [i for i in results]
    logging.info(
        f" is it the original length equal to the generated answers? {len(all_results) == sum(1 for _ in docs_for_len_1)}")
    # Save all results into a JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        pass
    json.dump(all_results, f, ensure_ascii=False, indent=2)

