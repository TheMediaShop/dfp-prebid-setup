from googleads import dfp
import yaml

import settings


def get_client():
    # Build the Yaml file from scratch so we can move the settings into the application level
    return dfp.DfpClient.LoadFromString(yaml.dump(settings.GOOGLEADS_YAML))
