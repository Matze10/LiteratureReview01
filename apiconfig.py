from pybliometrics.scopus.utils import create_config

#Correct configuration of the API KEYS 
def load_api_keys(file_path):
    """
    Load API keys from a text file.

    Args:
        file_path (str): Path to the text file containing the API keys.

    Returns:
        list: List of API keys.
    """
    with open(file_path, 'r') as file:
        api_keys = [line.strip() for line in file.readlines()]
    return api_keys
