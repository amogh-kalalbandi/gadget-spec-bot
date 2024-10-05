if 'custom' not in globals():
    from mage_ai.data_preparation.decorators import custom
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm.auto import tqdm
import requests

GADGETS_360_URL = "https://www.gadgets360.com/mobiles"
BRANDS_URL = "all-brands"

def get_url_list_of_all_mobile_phone_brands():
    """Get the list of all URLs of all mobile phone brands."""

    web_doc_url = f"{GADGETS_360_URL}/{BRANDS_URL}"
    response = requests.get(web_doc_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
    else:
        print(f'get_url_list_of_all_mobile_phone_brands:Response received = {response.status_code}')

    brand_list = soup.find('div', class_="brand_list")

    ### Get the URLs of all the mobile phone brands listed on page.
    mobile_brand_list = brand_list.find('div', class_="brand")
    temp_mobile_brand_list = mobile_brand_list.find_all('a', class_="rvw-title")

    ### Create a list of all brands of mobile phones.
    mobile_urls = []
    for each_tag in temp_mobile_brand_list:
        if '-phones' in each_tag['href']:
            mobile_urls.append(each_tag['href'])

    return mobile_urls


def get_all_mobile_phones_under_a_brand(mobile_brand_url, errored_mobile_urls):
    """Get all URLs of phones under a brand URL."""
    response = requests.get(mobile_brand_url)

    if response.status_code == 200:
        ten_oh_html_doc = BeautifulSoup(response.content, 'html.parser')
    else:
        print(f'get_all_mobile_phones_under_a_brand:Response received = {response.status_code}')

    ### Add an if condition to the below statement. Move forward only if brand_list classname is present in html doc.
    mobile_list_element = ten_oh_html_doc.find('div', class_="brand_list")
    if mobile_list_element:
        mobile_list_divs = mobile_list_element.find_all('div', class_="rvw-imgbox")

        mobile_list_url = []

        for each_div in mobile_list_divs:
            a_tag = each_div.find('a')
            mobile_list_url.append(a_tag['href'])
        return mobile_list_url
    else:
        errored_mobile_urls.append(mobile_brand_url)
        return []


def get_mobile_specs(mobile_detail_url, mobile_specifications):
    """Get specifications of mobile phones"""
    ### Get the name of the mobile whose details are being extracted.
    mob_url = urlparse(mobile_detail_url)
    # mobile_name = '-'.join(mob_url.path.replace('/', '').split('-')[:-1])

    ### Get the list of all the mobile phones under a single brand.
    response = requests.get(mobile_detail_url)

    if response.status_code == 200:
        mobile_detail_soup = BeautifulSoup(response.content, 'html.parser')
    else:
        print(f'get_mobile_specs:Response received = {response.status_code}')

    # Find the mobile name in the document
    mobile_name = mobile_detail_soup.find('div', class_="_lhs").find('h1').text.lower().replace(' ', '-')

    ### find all the categories of specs defined for the mobile phone.
    detail_spec_div = mobile_detail_soup.select("div#specs")
    specs_category_divs = detail_spec_div[0].find_all('div', class_="_hd")

    ### Define a dictionary to collect all the details of mobile phones.
    mobile_specifications.update({ mobile_name: {} })

    ### Find details of the mobile phone and update it to a dictionary.
    for each_category in specs_category_divs:
        category_name = each_category.text
        mobile_specifications[mobile_name].update({ category_name: {} })

        #### Since the table of specs does not have any class to find, Traverse 2 parents up to find the right tag.
        category_table_data = each_category.parent.parent.find('table')
        table_rows = category_table_data.find_all('tr')

        for each_table_row in table_rows:
            table_data = each_table_row.find_all('td')
            if len(table_data) > 1:
                key = each_table_row.find_all('td')[0].text
                value = each_table_row.find_all('td')[1].text
                mobile_specifications[mobile_name][category_name].update({ key: value })

    return mobile_specifications


def get_all_mobile_specifications():
    """Get specifications of all mobile phones."""
    mobile_brand_url_list = get_url_list_of_all_mobile_phone_brands()
    mobile_specs_data_by_brand = {}
    errored_mobile_urls = []

    for each_mobile_brand_url in tqdm(mobile_brand_url_list):
        print(f"processing = {each_mobile_brand_url}")
        url_obj = urlparse(each_mobile_brand_url)
        brand_name = url_obj.path.split('/')[-1]
        mobile_phones_url_list = get_all_mobile_phones_under_a_brand(each_mobile_brand_url, errored_mobile_urls)
        temp_mobile_specifications = {}

        for each_mobile_phone in mobile_phones_url_list:
            temp_mobile_specifications = get_mobile_specs(each_mobile_phone, temp_mobile_specifications)
        mobile_specs_data_by_brand.update({ brand_name: temp_mobile_specifications })

    return mobile_specs_data_by_brand, errored_mobile_urls


@custom
def transform_custom(*args, **kwargs):
    """
    args: The output from any upstream parent blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    mobile_specs_data_by_brand, errored_mobile_urls = get_all_mobile_specifications()
    mobile_brand_list = list(mobile_specs_data_by_brand.keys())
    print(f"---------------")
    print(f"mobile_brand_list = {mobile_brand_list}")
    print(f"---------------")
    return mobile_specs_data_by_brand, errored_mobile_urls


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
