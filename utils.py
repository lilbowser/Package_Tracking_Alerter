import yaml


def load_api_config(config_file_name):
    with open(config_file_name) as config:
        return yaml.load(config)["api_keys"]