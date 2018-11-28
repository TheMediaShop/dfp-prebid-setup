from googleads import dfp

from dfp.client import get_client


def create_line_items(line_items):
    """
    Creates line items in DFP.

    Args:
      line_items (arr): an array of objects, each a line item configuration
    Returns:
      an array: an array of created line item IDs
    """
    dfp_client = get_client()
    line_item_service = dfp_client.GetService('LineItemService', version='v201802')
    line_items = line_item_service.createLineItems(line_items)

    # Return IDs of created line items.
    created_line_item_ids = []
    for line_item in line_items:
        created_line_item_ids.append(line_item['id'])
    return created_line_item_ids


def create_line_item_config(name, order_id, placement_ids, cpm_micro_amount,
                            sizes, hb_criteria,
                            currency_code='USD'):
    """
    Creates a line item config object.

    Args:
      name (str): the name of the line item
      order_id (int): the ID of the order in DFP
      placement_ids (arr): an array of DFP placement IDs to target
      cpm_micro_amount (int): the currency value (in micro amounts) of the
        line item
      sizes (arr): an array of objects, each containing 'width' and 'height'
        keys, to set the creative sizes this line item will serve
      hb_criteria (dict): An dict of key: value pairs for criteria for this line item
      currency_code (str): the currency code (e.g. 'USD' or 'EUR')
    Returns:
      an object: the line item config
    """

    # Set up sizes.
    creative_placeholders = []

    for size in sizes:
        creative_placeholders.append({
            'size': size
        })

    # Setup criteria
    bidder_criteria = []

    # Create key/value targeting for Prebid.
    # https://github.com/googleads/googleads-python-lib/blob/master/examples/dfp/v201802/line_item_service/target_custom_criteria.py
    # create custom criterias
    for criteria_key, criteria_value in hb_criteria.iteritems():
        bidder_criteria.append({
            'xsi_type': 'CustomCriteria',
            'keyId': criteria_key,
            'valueIds': [criteria_value],
            'operator': 'IS'
        })

    # https://developers.google.com/doubleclick-publishers/docs/reference/v201802/LineItemService.LineItem
    line_item_config = {
        'name': name,
        'orderId': order_id,
        # https://developers.google.com/doubleclick-publishers/docs/reference/v201802/LineItemService.Targeting
        'targeting': {
            'inventoryTargeting': {
                'targetedPlacementIds': placement_ids
            },
            'customTargeting': {
                'xsi_type': 'CustomCriteriaSet',
                'logicalOperator': 'AND',
                'children': bidder_criteria
            },
        },
        'startDateTimeType': 'IMMEDIATELY',
        'unlimitedEndDateTime': True,
        'lineItemType': 'PRICE_PRIORITY',
        'costType': 'CPM',
        'costPerUnit': {
            'currencyCode': currency_code,
            'microAmount': cpm_micro_amount
        },
        'creativeRotationType': 'EVEN',
        'primaryGoal': {
            'goalType': 'NONE'
        },
        'creativePlaceholders': creative_placeholders,
    }
    return line_item_config
