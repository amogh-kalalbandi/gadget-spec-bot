import os
import time
import json
import requests

# from openai import OpenAI
from huggingface_hub import InferenceClient
from elasticsearch import Elasticsearch

ELASTIC_URL = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

es_client = Elasticsearch(ELASTIC_URL)
hugging_face = InferenceClient("HuggingFaceH4/zephyr-7b-beta", token=HF_API_TOKEN)
print(f'Hugging client initialized = {hugging_face}')

relevance_client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.3", token=HF_API_TOKEN)
print(f'Hugging client initialized = {relevance_client}')


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
You are mobile phone expert. Follow the STRATEGIES given below on how to answer statement given by the user.
Print result in a markdown format where subsections are indented in readable format. DO NOT PRINT CODE 
to get the specifications of a mobile phone. PRINT what is passed in the CONTEXT.

STRATEGIES:

Case 1: If the user asks the question for eg:
    Tell me the specifications of a phone, then:
        The CONTEXT contains 5 results. Split the results on \n\n to get the results.
        Print only the first name, company and specifications of CONTEXT.
        DO NOT PRINT QUESTIONS WITH THE ANSWER. PRINT ONLY THE SPECIFICATIONS.

Case 2: If the user asks the question for eg:
    List all the phones under samsung brand, then:
        The CONTEXT contains 5 results. Split the results on \n\n to get the results.
        Print all the names of the mobile phones returned in the split results.
        Print only the BRAND AND MODEL information.

Case 3: If the user asks the question for eg:
    Which is the best phone with 128-megapixel camera, then:
        The CONTEXT contains 5 results. Split the results on \n\n to get the results.
        Pick the first result of the split and List down all the specifications of the first result present the CONTEXT.

PHONE: {phone}

CONTEXT:
{context}

Things to remember:
1. If the user asks for specifications, Do not give the whole answer, Extract and print only specifications.
2. If the user asks for list of phones, Extract only the phone names from CONTEXT and print.
3. Please ensure that the result is printed in the right format for the user to read.
4. DO NOT PRINT CODE to get the specifications of a mobile phone.
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
    # vector = model.encode(query)
    url = 'http://host.docker.internal:5000/vector'
    param_value = query

    # Create the parameters dictionary to send with the request
    params = {'input': param_value}

    # Send the GET request to the Flask app
    response = requests.get(url, params=params)
    mobile_context = elastic_search_knn(response.json()['vector'], 'specification_vector')

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