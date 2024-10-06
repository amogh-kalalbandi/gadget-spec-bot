import os
import time
import json

# from openai import OpenAI
from huggingface_hub import InferenceClient

from elasticsearch import Elasticsearch
# from sentence_transformers import SentenceTransformer
import spacy

ELASTIC_URL = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

es_client = Elasticsearch(ELASTIC_URL)
hugging_face = InferenceClient("HuggingFaceH4/zephyr-7b-beta", token=HF_API_TOKEN)
print(f'Hugging client initialized = {hugging_face}')

relevance_client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.3", token=HF_API_TOKEN)
print(f'Hugging client initialized = {relevance_client}')

# model = SentenceTransformer("all-mpnet-base-v2")
nlp = spacy.load('en_core_web_sm')

def elastic_search_knn(vector, vector_field, index_name="mobile-specifications"):
    """Return elastic search results for given vector."""
    knn_query = {
        "field": vector_field,
        "query_vector": vector,
        "k": 5,
        "num_candidates": 10000
    }

    search_query = {
        'knn': knn_query,
        '_source': ["name", "company", "specifications"]
    }

    es_results = es_client.search(
        index=index_name,
        body=search_query
    )

    result_docs = []

    for hit in es_results['hits']['hits']:
        result_docs.append(hit['_source'])

    return result_docs


def build_prompt(phone_specifications, mobile_context):
    """Build the context using search results and return the prompt."""
    prompt_template = """
You are mobile phone expert. Answer all the questions of PHONE using the CONTEXT provided from SPECFICATIONS database.
The specifications in the CONTEXT is a json string. Convert the json string to readable format before printing out the answer.
Use only the specifications given in the context to print the specs of the device.
Do not number the specifications passed.
Print only the first result in a markdown format where subsections are indented in readable format.

Case 1: If the user asks the question for eg:
    Tell me the specifications of the iphone 12, then:
        List down all the specifications of the first result present the CONTEXT.

Case 2: If the user asks the question for eg:
    List all the phones under samsung brand, then:
        Print all the names of the mobile phones returned in the CONTEXT.
        Print only the BRAND AND MODEL information.


PHONE: {phone}

CONTEXT:
{context}
""".strip()

    context = ""

    for each in mobile_context:
        context = context + f"\n\nname: {each['name']}\ncompany: {each['company']}\nspecifications: {each['specifications']}"

    prompt = prompt_template.format(phone=phone_specifications, context=context)
    return prompt


def evaluate_relevance(statement, answer):
    prompt_template = """
    You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.
    Your task is to analyze the relevance of the generated answer to the given question or statement.
    Based on the relevance of the generated answer, you will classify it
    as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

    Here is the data for evaluation:

    Statement: {statement}
    Generated Answer: {answer}

    Please analyze the content and context of the generated answer in relation to the question
    and provide your evaluation in parsable JSON without using code blocks:

    {{
      "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
      "Explanation": "[Provide a brief explanation for your evaluation]"
    }}
    """.strip()

    prompt = prompt_template.format(statement=statement, answer=answer)
    evaluation, tokens, _ = llm('mistral', relevance_client, prompt)

    try:
        json_eval = json.loads(evaluation)
        return json_eval['Relevance'], json_eval['Explanation'], tokens
    except json.JSONDecodeError:
        return "UNKNOWN", "Failed to parse evaluation", tokens


def llm(model, client, prompt):
    """Return LLM generation based on context."""
    start_time = time.time()
    messages = [{"role": "user", "content": prompt}]
    response = client.chat_completion(messages, max_tokens=1000)
    answer = response.choices[0].message.content
    tokens = {
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
        'total_tokens': response.usage.total_tokens
    }

    end_time = time.time()
    response_time = end_time - start_time

    return answer, tokens, response_time


def get_answer(query, model_choice):
    vector = model.encode(query)
    mobile_context = elastic_search_knn(vector, 'specification_vector')

    prompt = build_prompt(query, mobile_context)
    print(f'Prompt built = {prompt}')
    answer, tokens, response_time = llm('zephyr', hugging_face, prompt)

    relevance, explanation, eval_tokens = evaluate_relevance(query, answer)

    # openai_cost = calculate_openai_cost(model_choice, tokens)

    return {
        'answer': answer,
        'response_time': response_time,
        'relevance': relevance,
        'relevance_explanation': explanation,
        'model_used': model_choice,
        'prompt_tokens': tokens['prompt_tokens'],
        'completion_tokens': tokens['completion_tokens'],
        'total_tokens': tokens['total_tokens'],
        'eval_prompt_tokens': eval_tokens['prompt_tokens'],
        'eval_completion_tokens': eval_tokens['completion_tokens'],
        'eval_total_tokens': eval_tokens['total_tokens'],
        # 'openai_cost': openai_cost
    }