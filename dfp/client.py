from googleads import dfp
import yaml

import settings


def get_client():
    # Build the Yaml file from scratch so we can move the settings into the application level
    yaml_data = {
        'dfp': {
            'application_name': settings.DFP_APPLICATION_NAME,
            'network_code': settings.DFP_NETWORK_CODE,
            'path_to_private_key_file': settings.DFP_CREDENTIALS_JSON
        }
    }

    return dfp.DfpClient.LoadFromString(yaml.dump(yaml_data))
