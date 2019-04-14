import logging
import os
import sys
from builtins import input
from pprint import pprint

from colorama import init

import settings
import dfp.associate_line_items_and_creatives
import dfp.create_custom_targeting
import dfp.create_creatives
import dfp.create_line_items
import dfp.create_orders
import dfp.get_ad_units
import dfp.get_advertisers
import dfp.get_custom_targeting
import dfp.get_placements
import dfp.get_users
from dfp.exceptions import (
    BadSettingException,
    MissingSettingException
)
from tasks.price_utils import (
    get_prices_array,
    get_prices_summary_string,
    micro_amount_to_num,
    num_to_str,
)

# Colorama for cross-platform support for colored logging.
# https://github.com/kmjennison/dfp-prebid-setup/issues/9
init()

# Configure logging.
if 'DISABLE_LOGGING' in os.environ and os.environ['DISABLE_LOGGING'] == 'true':
    logging.disable(logging.CRITICAL)
    logging.getLogger('googleads').setLevel(logging.CRITICAL)
    logging.getLogger('oauth2client').setLevel(logging.CRITICAL)
else:
    FORMAT = '%(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=FORMAT)
    logging.getLogger('googleads').setLevel(logging.ERROR)
    logging.getLogger('oauth2client').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


def setup_partner(user_email, advertiser_name, order_name, placements,
                  sizes, bidder_code, prices, num_creatives, currency_code, hb_criteria_custom, hb_bidder=True,
                  creative_template_id=None):
    """
    Call all necessary DFP tasks for a new Prebid partner setup.
    """

    # Get the user.
    user_id = dfp.get_users.get_user_id_by_email(user_email)

    # Get the placement IDs.
    placement_ids = dfp.get_placements.get_placement_ids_by_name(placements)

    # Get (or potentially create) the advertiser.
    advertiser_id = dfp.get_advertisers.get_advertiser_id_by_name(
        advertiser_name)

    # Create the order.
    order_id = dfp.create_orders.create_order(order_name, advertiser_id, user_id)

    # Define the criteria we want to pass to the line items when they are created
    hb_criteria = {}

    # Do custom hb_criteria
    for criteria_key, criteria_value in hb_criteria_custom.iteritems():
        key_id = get_or_create_dfp_targeting_key(criteria_key)
        hb_criteria[key_id] = DFPValueIdGetter(criteria_key).get_value_id(criteria_value)

    # We have a specific bidder criteria, create and add it
    if hb_bidder:
        hb_bidder_key_id = get_or_create_dfp_targeting_key('hb_bidder')
        HBBidderValueGetter = DFPValueIdGetter('hb_bidder')
        hb_criteria[hb_bidder_key_id] = HBBidderValueGetter.get_value_id(bidder_code)

    # Get DFP key IDs for line item targeting.
    hb_pb_key_id = get_or_create_dfp_targeting_key('hb_pb')
    HBPBValueGetter = DFPValueIdGetter('hb_pb')

    # Create line item config(s).

    logger.info("Creating line item config(s)...")
    line_items_config = create_line_item_configs(prices, order_id,
                                                 placement_ids, bidder_code, sizes, hb_pb_key_id,
                                                 currency_code, hb_criteria, HBPBValueGetter,
                                                 creative_template_id=creative_template_id)

    logger.info("Creating line items...")
    line_item_ids = dfp.create_line_items.create_line_items(line_items_config)

    # Create creative(s).
    if creative_template_id is not None:
        logger.info("Building Native ad creative config...")
        creative_config = dfp.create_creatives.create_native_creative_config(
            bidder_code=bidder_code,
            order_name=order_name,
            advertiser_id=advertiser_id,
            creative_template_id=creative_template_id
        )

        # No sizes since we are Native
        sizes = None

    else:
        logger.info("Building creative config(s)...")
        creative_config = dfp.create_creatives.create_duplicate_creative_configs(
            bidder_code=bidder_code,
            order_name=order_name,
            advertiser_id=advertiser_id,
            prebid_creative_snippet=settings.PREBID_CREATIVE_SNIPPET,
            num_creatives=num_creatives)

    logger.info("Creating creatives...")
    creative_ids = dfp.create_creatives.create_creatives(creative_config)

    # Associate creatives with line items.
    logger.info("Associating creative(s) and line item(s)...")
    dfp.associate_line_items_and_creatives.make_licas(
        line_item_ids=line_item_ids,
        creative_ids=creative_ids,
        sizes=sizes)

    logger.info("""

    Done! Please review your order, line items, and creatives to
    make sure they are correct. Then, approve the order in DFP.

    Happy bidding!

  """)


class DFPValueIdGetter(object):
    """
    A class to bulk fetch DFP values by key and then create new values as needed.
    """

    def __init__(self, key_name, *args, **kwargs):
        """
        Args:
          key_name (str): the name of the DFP key
        """
        self.key_name = key_name
        self.key_id = dfp.get_custom_targeting.get_key_id_by_name(key_name)
        self.existing_values = dfp.get_custom_targeting.get_targeting_by_key_name(
            key_name)
        super(DFPValueIdGetter, self).__init__(*args, **kwargs)

    def _get_value_id_from_cache(self, value_name):
        val_id = None
        for value_obj in self.existing_values:
            if value_obj['name'] == value_name:
                val_id = value_obj['id']
                break
        return val_id

    def _create_value_and_return_id(self, value_name):
        return dfp.create_custom_targeting.create_targeting_value(value_name,
                                                                  self.key_id)

    def get_value_id(self, value_name):
        """
        Get the DFP custom value ID, or create it if it doesn't exist.

        Args:
          value_name (str): the name of the DFP value
        Returns:
          an integer: the ID of the DFP value
        """
        val_id = self._get_value_id_from_cache(value_name)
        if not val_id:
            val_id = self._create_value_and_return_id(value_name)
        return val_id


def get_or_create_dfp_targeting_key(name):
    """
    Get or create a custom targeting key by name.

    Args:
      name (str)
    Returns:
      an integer: the ID of the targeting key
    """
    key_id = dfp.get_custom_targeting.get_key_id_by_name(name)
    if key_id is None:
        key_id = dfp.create_custom_targeting.create_targeting_key(name)
    return key_id


def create_line_item_configs(prices, order_id, placement_ids, bidder_code,
                             sizes, hb_pb_key_id, currency_code, hb_criteria,
                             HBPBValueGetter, creative_template_id):
    """
    Create a line item config for each price bucket.

    Args:
      prices (array)
      order_id (int)
      placement_ids (arr)
      bidder_code (str)
      hb_bidder_key_id (int)
      hb_pb_key_id (int)
      currency_code (str)
      hb_criteria (dict)
      HBPBValueGetter (DFPValueIdGetter)
      creative_template_id
    Returns:
      an array of objects: the array of DFP line item configurations
    """

    line_items_config = []
    for price in prices:
        price_str = num_to_str(micro_amount_to_num(price))

        # Autogenerate the line item name.
        line_item_name = u'{bidder_code}: HB ${price}'.format(
            bidder_code=bidder_code,
            price=price_str
        )

        # The DFP targeting value ID for this `hb_pb` price value.
        hb_pb_value_id = HBPBValueGetter.get_value_id(price_str)

        # Add the prebid key and price to the criteria
        hb_criteria[hb_pb_key_id] = hb_pb_value_id

        # Create the line item config
        config = dfp.create_line_items.create_line_item_config(
            name=line_item_name,
            order_id=order_id,
            placement_ids=placement_ids,
            cpm_micro_amount=price,
            sizes=sizes,
            hb_criteria=hb_criteria,
            currency_code=currency_code,
            creative_template_id=creative_template_id,
        )

        line_items_config.append(config)

    return line_items_config


def check_price_buckets_validity(price_buckets):
    """
    Validate that the price_buckets object contains all required keys and the
    values are the expected types.

    Args:
      price_buckets (object)
    Returns:
      None
    """

    try:
        pb_precision = price_buckets['precision']
        pb_min = price_buckets['min']
        pb_max = price_buckets['max']
        pb_increment = price_buckets['increment']
    except KeyError:
        raise BadSettingException('The setting "PREBID_PRICE_BUCKETS" '
                                  'must contain keys "precision", "min", "max", and "increment".')

    if not (isinstance(pb_precision, int) or isinstance(pb_precision, float)):
        raise BadSettingException('The "precision" key in "PREBID_PRICE_BUCKETS" '
                                  'must be a number.')

    if not (isinstance(pb_min, int) or isinstance(pb_min, float)):
        raise BadSettingException('The "min" key in "PREBID_PRICE_BUCKETS" '
                                  'must be a number.')

    if not (isinstance(pb_max, int) or isinstance(pb_max, float)):
        raise BadSettingException('The "max" key in "PREBID_PRICE_BUCKETS" '
                                  'must be a number.')

    if not (isinstance(pb_increment, int) or isinstance(pb_increment, float)):
        raise BadSettingException('The "increment" key in "PREBID_PRICE_BUCKETS" '
                                  'must be a number.')


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def main():
    """
    Validate the settings and ask for confirmation from the user. Then,
    start all necessary DFP tasks.
    """

    user_email = getattr(settings, 'DFP_USER_EMAIL_ADDRESS', None)
    if user_email is None:
        raise MissingSettingException('DFP_USER_EMAIL_ADDRESS')

    advertiser_name = getattr(settings, 'DFP_ADVERTISER_NAME', None)
    if advertiser_name is None:
        raise MissingSettingException('DFP_ADVERTISER_NAME')

    order_name = getattr(settings, 'DFP_ORDER_NAME', None)
    if order_name is None:
        raise MissingSettingException('DFP_ORDER_NAME')

    placements = getattr(settings, 'DFP_TARGETED_PLACEMENT_NAMES', None)
    if placements is None:
        raise MissingSettingException('DFP_TARGETED_PLACEMENT_NAMES')
    elif len(placements) < 1:
        raise BadSettingException('The setting "DFP_TARGETED_PLACEMENT_NAMES" '
                                  'must contain at least one DFP placement ID.')

    sizes = getattr(settings, 'DFP_PLACEMENT_SIZES', None)
    if sizes is None:
        raise MissingSettingException('DFP_PLACEMENT_SIZES')
    elif len(sizes) < 1:
        raise BadSettingException('The setting "DFP_PLACEMENT_SIZES" '
                                  'must contain at least one size object.')

    currency_code = getattr(settings, 'DFP_CURRENCY_CODE', 'USD')
    if currency_code is None:
        raise MissingSettingException('DFP_CURRENCY_CODE')

    # How many creatives to attach to each line item. We need at least one
    # creative per ad unit on a page. See:
    # https://github.com/kmjennison/dfp-prebid-setup/issues/13
    num_creatives = (
            getattr(settings, 'DFP_NUM_CREATIVES_PER_LINE_ITEM', None) or
            len(placements)
    )

    bidder_code = getattr(settings, 'PREBID_BIDDER_CODE', None)
    if bidder_code is None:
        hb_bidder = False
        # No specific bidder code, use generic Prebid value. This will NOT be created as a key:value pair
        bidder_code = 'Prebid'
    else:
        hb_bidder = True

    hb_criteria = getattr(settings, 'PREBID_CRITERIA', {})

    price_buckets = getattr(settings, 'PREBID_PRICE_BUCKETS', None)
    if price_buckets is None:
        raise MissingSettingException('PREBID_PRICE_BUCKETS')

    check_price_buckets_validity(price_buckets)

    prices = get_prices_array(price_buckets)
    prices_summary = get_prices_summary_string(prices,
                                               price_buckets['precision'])

    # Are we native?
    creative_template_id = settings.PREBID_NATIVE_FORMAT_ID if settings.PREBID_NATIVE else None

    logger.info(
        u"""
    
        Going to create {name_start_format}{num_line_items}{format_end} new line items.
          {name_start_format}Order{format_end}: {value_start_format}{order_name}{format_end}
          {name_start_format}Advertiser{format_end}: {value_start_format}{advertiser}{format_end}
          {name_start_format}Native Ad Units?{format_end}: {value_start_format}{native}{format_end}
    
        Line items will have targeting:
          {name_start_format}Currency{format_end} = {value_start_format}{currency_code}{format_end}
          {name_start_format}hb_pb{format_end} = {value_start_format}{prices_summary}{format_end}
          {name_start_format}hb_bidder{format_end} = {value_start_format}{bidder_code}{format_end}
          {name_start_format}placements{format_end} = {value_start_format}{placements}{format_end}
    
        """.format(
            num_line_items=len(prices),
            order_name=order_name,
            advertiser=advertiser_name,
            user_email=user_email,
            prices_summary=prices_summary,
            bidder_code=bidder_code,
            placements=placements,
            sizes=sizes,
            native=creative_template_id is not None,
            currency_code=currency_code,
            name_start_format=color.BOLD,
            format_end=color.END,
            value_start_format=color.BLUE,
        ))

    ok = input('Is this correct? (y/n)\n')

    if ok != 'y':
        logger.info('Exiting.')
        return

    setup_partner(
        user_email,
        advertiser_name,
        order_name,
        placements,
        sizes,
        bidder_code,
        prices,
        num_creatives,
        currency_code,
        hb_criteria,
        hb_bidder,
        creative_template_id=creative_template_id
    )


if __name__ == '__main__':
    main()
