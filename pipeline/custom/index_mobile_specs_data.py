if 'custom' not in globals():
    from mage_ai.data_preparation.decorators import custom
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

import json
from elasticsearch import Elasticsearch
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer

index_settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "company": {"type": "text"},
            "name": {"type": "text"},
            "specifications": {"type": "keyword"},
            "specification_vector": {"type": "dense_vector", "dims": 768, "index": True, "similarity": "cosine"}
        }
    }
}


def transform_and_index_mobile_data_to_es(es_client, index_name, mobile_specs_data):
    """Convert the specifications to json string and index the data"""
    mobile_specs_rows = []
    model = SentenceTransformer("all-mpnet-base-v2")

    print("Converting specifications to JSON string")
    for each_mobile_company in tqdm(mobile_specs_data):
        for each_mobile in mobile_specs_data[each_mobile_company]:
            temp_mobile_dictionary = {
                'company': each_mobile_company,
                'name': each_mobile,
                'specifications': json.dumps(mobile_specs_data[each_mobile_company][each_mobile])
            }
            mobile_specs_rows.append(temp_mobile_dictionary)

    for each_mobile in tqdm(mobile_specs_rows):
        each_mobile['specification_vector'] = model.encode(each_mobile['specifications']).tolist()

    print("Specifications modified and encoded.")

    for doc in tqdm(mobile_specs_rows):
        es_client.index(index=index_name, document=doc)

    print("Data indexed to Elastic search.")
    return True


@custom
def transform_custom(*args, **kwargs):
    """
    args: The output from any upstream parent blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    # Specify your custom logic here
    es_client = Elasticsearch('elasticsearch:9200')
    print('--------------')
    print(es_client.info())
    print('--------------')
    index_name = "mobile-specifications"

    # Read the mobile specs data from JSON file.
    with open('/app/data-extraction/all_mobiles_specs_data_by_brand.json', 'r') as fp:
        mobile_specs_data = json.load(fp)

    # Check if index exists, if yes, then delete the index.
    if es_client.indices.exists(index=index_name):
        es_client.indices.delete(index=index_name)

    es_client.indices.create(index=index_name, body=index_settings)
    response = transform_and_index_mobile_data_to_es(es_client, index_name, mobile_specs_data)

    return response


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
