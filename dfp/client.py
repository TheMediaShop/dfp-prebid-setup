from googleads import ad_manager
import yaml

import settings


def get_client():
    # Build the Yaml file from scratch so we can move the settings into the application level
    return ad_manager.AdManagerClient.LoadFromString(yaml.dump(settings.GOOGLEADS_YAML))
