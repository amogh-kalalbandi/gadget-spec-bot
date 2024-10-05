if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

import json


@transformer
def transform(data, *args, **kwargs):
    """
    Template code for a transformer block.

    Add more parameters to this function if this block has multiple parent blocks.
    There should be one parameter for each output variable from each parent block.

    Args:
        data: The output from the upstream parent block
        args: The output from any additional upstream blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    # Specify your transformation logic here
    print(data)
    mobile_specs_data_by_brand = data['mobile_specs_data_by_brand']
    errored_mobile_specs_data_by_brand = data['errored_mobile_specs_data_by_brand']

    # Combine the data from both specifications dictionary
    all_mobiles_specs_data_by_brand = mobile_specs_data_by_brand | errored_mobile_specs_data_by_brand

    with open('/app/data-extraction/all_mobiles_specs_data_by_brand.json', 'w+') as fp:
        json.dump(all_mobiles_specs_data_by_brand, fp)

    return True


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
