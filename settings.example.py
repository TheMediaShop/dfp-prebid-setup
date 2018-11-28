import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

#########################################################################
# DFP SETTINGS
#########################################################################

# YAML File settings
GOOGLEADS_YAML = {
    'dfp': {
        'application_name': 'INSERT_APPLICATION_NAME_HERE',
        'network_code': 'INSERT_NETWORK_CODE_HERE',
        'path_to_private_key_file': './key.json'
    }
}
# End YAML File settings

# A string describing the order
DFP_ORDER_NAME = None

# The email of the DFP user who will be the trafficker for
# the created order
DFP_USER_EMAIL_ADDRESS = None

# The exact name of the DFP advertiser for the created order
DFP_ADVERTISER_NAME = None

# Names of placements the line items should target.
DFP_TARGETED_PLACEMENT_NAMES = []

# Sizes of placements. These are used to set line item and creative sizes.
DFP_PLACEMENT_SIZES = [
    {
        'width': '300',
        'height': '250'
    },
    {
        'width': '728',
        'height': '90'
    },
]

# Whether we should create the advertiser in DFP if it does not exist.
# If False, the program will exit rather than create an advertiser.
DFP_CREATE_ADVERTISER_IF_DOES_NOT_EXIST = False

# If settings.DFP_ORDER_NAME is the same as an existing order, add the created
# line items to that order. If False, the program will exit rather than
# modify an existing order.
DFP_USE_EXISTING_ORDER_IF_EXISTS = False

# Optional
# Each line item should have at least as many creatives as the number of
# ad units you serve on a single page because DFP specifies:
#   "Each of a line item's assigned creatives can only serve once per page,
#    so if you want the same creative to appear more than once per page,
#    copy the creative to associate multiple instances of the same creative."
# https://support.google.com/dfp_sb/answer/82245?hl=en
#
# This will default to the number of placements specified in
# `DFP_TARGETED_PLACEMENT_NAMES`.
# DFP_NUM_CREATIVES_PER_LINE_ITEM = 2

# Optional
# The currency to use in DFP when setting line item CPMs. Defaults to 'USD'.
# DFP_CURRENCY_CODE = 'USD'

#########################################################################
# PREBID SETTINGS
#########################################################################

# The bidder code for hb_bidder criteria, set to None to disable and not use specific bidder criteria for the line items
PREBID_BIDDER_CODE = None

# Template used when creating the creatives for each ad unit size
PREBID_CREATIVE_SNIPPET = './dfp/creative_snippet.html'

# Price buckets. This should match your Prebid settings for the partner. See:
# http://prebid.org/dev-docs/publisher-api-reference.html#module_pbjs.setPriceGranularity
# FIXME: this should be an array of buckets. See:
# https://github.com/prebid/Prebid.js/blob/8fed3d7aaa814e67ca3efc103d7d306cab8c692c/src/cpmBucketManager.js
PREBID_PRICE_BUCKETS = {
    'precision': 2,
    'min': 0,
    'max': 20,
    'increment': 0.10,
}

# Extra criteria we want added to our line items (key: value pairs) (AND criteria only)
PREBID_CRITERIA = {
    #'hb_format': 'display'
}

#########################################################################

# Try importing local settings, which will take precedence.
try:
    from local_settings import *
except ImportError:
    pass
