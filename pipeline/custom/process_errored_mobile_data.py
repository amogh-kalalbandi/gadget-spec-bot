if 'custom' not in globals():
    from mage_ai.data_preparation.decorators import custom
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm.auto import tqdm
import requests
import json

from pipeline.custom.scrape_and_create_ndtv_website_data import get_mobile_specs


def get_mobile_urls_of_brand(bad_urls, mobile_listing_url):
    """Get detail URLs of each mobile under a given brand."""
    mobile_detail_urls = []
    response = requests.get(mobile_listing_url)
    if response.status_code == 200:
        mobile_detail_soup = BeautifulSoup(response.content, 'html.parser')
    else:
        bad_urls.append(mobile_listing_url)

    mobile_listing_section = mobile_detail_soup.find('section', class_="_lpdlst")
    mobile_listing_div = mobile_listing_section.select('div#allplist')
    listing = mobile_listing_div[0].find_all('div', class_="_nolpoptbuy")

    for each_listing in listing:
        temp_mobile_detail_url = each_listing.find('h3', class_="_hd").find('a').get('href')
        mobile_detail_urls.append(temp_mobile_detail_url)

    return mobile_detail_urls


def process_errored_mobile_listing_urls(errored_mobile_specs_data_by_brand, errored_mobile_urls):
    """Processing the different HTML format."""
    bad_urls = []
    for each_listing_url in tqdm(errored_mobile_urls):
        mobile_detail_urls_list = get_mobile_urls_of_brand(bad_urls, each_listing_url)
        url_obj = urlparse(each_listing_url)
        brand_name = url_obj.path.split('/')[-1]
        temp_mobile_specifications = {}

        for each_mobile_detail_url in mobile_detail_urls_list:
            temp_mobile_specifications = get_mobile_specs(each_mobile_detail_url, temp_mobile_specifications)
            errored_mobile_specs_data_by_brand.update({ brand_name: temp_mobile_specifications })
    return errored_mobile_specs_data_by_brand, bad_urls


@custom
def transform_custom(*args, **kwargs):
    """
    args: The output from any upstream parent blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    # Specify your custom logic here
    mobile_specs_data_by_brand = args[0][0]
    errored_mobile_urls = args[0][1]
    errored_mobile_specs_data_by_brand = {}
    print(f'errored_mobile_urls = {errored_mobile_urls}')
    errored_mobile_specs_data_by_brand, bad_urls = process_errored_mobile_listing_urls(errored_mobile_specs_data_by_brand, errored_mobile_urls)
    mobile_brand_list = list(errored_mobile_specs_data_by_brand.keys())
    print("---------------")
    print(f"errored mobile_brand_list = {mobile_brand_list}")
    print("---------------")
    print(f"bad_urls = {bad_urls}")
    print("---------------")

    all_mobiles_specs_data_by_brand = mobile_specs_data_by_brand | errored_mobile_specs_data_by_brand

    with open('/app/data-extraction/all_mobiles_specs_data_by_brand.json', 'w+') as fp:
        json.dump(all_mobiles_specs_data_by_brand, fp)

    return mobile_specs_data_by_brand, errored_mobile_specs_data_by_brand


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
