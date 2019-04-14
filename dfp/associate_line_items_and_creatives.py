import logging

from dfp.client import get_client

logger = logging.getLogger(__name__)


def make_licas(line_item_ids, creative_ids, sizes):
    """
    Attaches creatives to line items in DFP.

    Args:
      line_item_ids (arr): an array of line item IDs
      creative_ids (arr): an array of creative IDs
      sizes (arr): an array of sizes or None for Native ad
    Returns:
      None
    """
    dfp_client = get_client()
    lica_service = dfp_client.GetService(
        'LineItemCreativeAssociationService', version='v201811')

    licas = []
    for line_item_id in line_item_ids:
        for creative_id in creative_ids:
            licas.append({
                'creativeId': creative_id,
                'lineItemId': line_item_id,
                # "Overrides the value set for Creative.size, which allows the
                #   creative to be served to ad units that would otherwise not be
                #   compatible for its actual size."
                #    https://developers.google.com/doubleclick-publishers/docs/reference/v201811/LineItemCreativeAssociationService.LineItemCreativeAssociation
                #
                # This is equivalent to selecting "Size overrides" in the DFP creative
                # settings, as recommended: http://prebid.org/adops/step-by-step.html
                'sizes': sizes
            })
    licas = lica_service.createLineItemCreativeAssociations(licas)

    if licas:
        logger.info(
            u'Created {0} line item <> creative associations.'.format(len(licas)))
    else:
        logger.info(u'No line item <> creative associations created.')
