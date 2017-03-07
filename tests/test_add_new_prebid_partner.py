
from unittest import TestCase

from mock import MagicMock, patch

import settings
import tasks.add_new_prebid_partner
from dfp.exceptions import BadSettingException, MissingSettingException
from tasks.price_utils import (
  get_prices_array,
)

email = 'fakeuser@example.com'
advertiser = 'My Advertiser'
order = 'My Cool Order'
placements = ['My Site Leaderboard', 'Another Placement']
bidder_code = 'mypartner'
price_buckets = {
  'precision': 2,
  'min' : 0,
  'max' : 20,
  'increment': 0.10,
}
prices = get_prices_array(price_buckets)

@patch.multiple('settings',
  DFP_USER_EMAIL_ADDRESS=email,
  DFP_ADVERTISER_NAME=advertiser,
  DFP_ORDER_NAME=order,
  DFP_TARGETED_PLACEMENT_NAMES=placements,
  PREBID_BIDDER_CODE=bidder_code,
  PREBID_PRICE_BUCKETS=price_buckets,
  DFP_CREATE_ADVERTISER_IF_DOES_NOT_EXIST=False)
@patch('googleads.dfp.DfpClient.LoadFromStorage')
class AddNewPrebidPartnerTests(TestCase):

  def test_missing_email_setting(self, mock_dfp_client):
    """
    It throws an exception with a missing setting.
    """
    settings.DFP_USER_EMAIL_ADDRESS = None
    with self.assertRaises(MissingSettingException):
      tasks.add_new_prebid_partner.main()

  def test_missing_advertiser_setting(self, mock_dfp_client):
    """
    It throws an exception with a missing setting.
    """
    settings.DFP_ADVERTISER_NAME = None
    with self.assertRaises(MissingSettingException):
      tasks.add_new_prebid_partner.main()

  def test_missing_order_setting(self, mock_dfp_client):
    """
    It throws an exception with a missing setting.
    """
    settings.DFP_ORDER_NAME = None
    with self.assertRaises(MissingSettingException):
      tasks.add_new_prebid_partner.main()


  def test_missing_placement_setting(self, mock_dfp_client):
    """
    It throws an exception with a missing setting.
    """
    settings.DFP_TARGETED_PLACEMENT_NAMES = None
    with self.assertRaises(MissingSettingException):
      tasks.add_new_prebid_partner.main()


  def test_missing_bidder_code_setting(self, mock_dfp_client):
    """
    It throws an exception with a missing setting.
    """
    settings.PREBID_BIDDER_CODE = None
    with self.assertRaises(MissingSettingException):
      tasks.add_new_prebid_partner.main()

  def test_price_bucket_validity_missing_key(self, mock_dfp_client):
    """
    It throws an exception of the price bucket setting
    is missing keys.
    """
    settings.PREBID_PRICE_BUCKETS={
      'precision': 2,
      'min' : 0,
      # 'max' : 20, # missing this key
      'increment': 0.10,
    }
    with self.assertRaises(BadSettingException):
      tasks.add_new_prebid_partner.main()

  def test_price_bucket_validity_bad_values(self, mock_dfp_client):
    """
    It throws an exception of the price bucket setting
    has bad value types.
    """
    settings.PREBID_PRICE_BUCKETS={
      'precision': 2,
      'min' : '$0', # bad value type
      'max' : 20,
      'increment': 0.10,
    }
    with self.assertRaises(BadSettingException):
      tasks.add_new_prebid_partner.main()

  def test_price_bucket_validity_bad_values_again(self, mock_dfp_client):
    """
    It throws an exception of the price bucket setting
    has bad value types.
    """
    settings.PREBID_PRICE_BUCKETS={
      'precision': 2,
      'min' : 0,
      'max' : 20,
      'increment': {'inc': 0.10}, # bad value type
    }
    with self.assertRaises(BadSettingException):
      tasks.add_new_prebid_partner.main()

  @patch('tasks.add_new_prebid_partner.setup_partner')
  @patch('tasks.add_new_prebid_partner.raw_input', return_value='n')
  def test_user_confirmation_rejected(self, mock_raw_input, 
    mock_setup_partners, mock_dfp_client):
    """
    Make sure we exit when the user rejects the confirmation.
    """
    tasks.add_new_prebid_partner.main()
    mock_setup_partners.assert_not_called()

  @patch('tasks.add_new_prebid_partner.setup_partner')
  @patch('tasks.add_new_prebid_partner.raw_input', return_value='asdf')
  def test_user_confirmation_not_accepted(self, mock_raw_input, 
    mock_setup_partners, mock_dfp_client):
    """
    Make sure we exit when the user types something other than 'y'.
    """
    tasks.add_new_prebid_partner.main()
    mock_setup_partners.assert_not_called()

  @patch('tasks.add_new_prebid_partner.setup_partner')
  @patch('tasks.add_new_prebid_partner.raw_input', return_value='y')
  def test_user_confirmation_accepted(self, mock_raw_input, 
    mock_setup_partners, mock_dfp_client):
    """
    Make sure we start the process when the user confirms we should proceed.
    """
    tasks.add_new_prebid_partner.main()
    mock_setup_partners.assert_called_once_with(email, advertiser, order,
      placements, bidder_code, prices)

  @patch('dfp.create_creatives')
  @patch('dfp.create_line_items')
  @patch('dfp.create_orders')
  @patch('dfp.get_advertisers')
  @patch('dfp.get_placements')
  @patch('dfp.get_users')
  def test_setup_partner(self, mock_get_users, mock_get_placements,
    mock_get_advertisers, mock_create_orders, mock_create_line_items,
    mock_create_creatives, mock_dfp_client):
    """
    It calls all expected DFP functions.
    """

    mock_get_users.get_user_id_by_email = MagicMock(return_value=14523)
    mock_get_placements.get_placement_ids_by_name = MagicMock(
      return_value=[1234567, 9876543])
    mock_get_advertisers.get_advertiser_id_by_name = MagicMock(
      return_value=246810)
    mock_create_orders.create_order = MagicMock(return_value=1357913)

    tasks.add_new_prebid_partner.setup_partner(
      user_email=email,
      advertiser_name=advertiser,
      order_name=order,
      placements=placements,
      bidder_code=bidder_code,
      prices=prices,
    )

    mock_get_users.get_user_id_by_email.assert_called_once_with(email)
    mock_get_placements.get_placement_ids_by_name.assert_called_once_with(
      placements)
    mock_get_advertisers.get_advertiser_id_by_name.assert_called_once_with(
      advertiser)
    mock_create_orders.create_order.assert_called_once_with(order, 246810,
      14523)
    mock_create_creatives.create_creatives.assert_called_once()
    mock_create_line_items.create_line_items.assert_called_once()


  def test_create_line_item_configs(self, mock_dfp_client):
    """
    It creates the expected line item configs.
    """

    configs = tasks.add_new_prebid_partner.create_line_item_configs(
      prices=[100000, 200000, 300000],
      order_id=1234567,
      placement_ids=[9876543, 1234567],
      advertiser_name='Wonderful Ad Partner'
    )

    self.assertEqual(len(configs), 3)

    self.assertEqual(configs[0]['name'], 'Wonderful Ad Partner: HB $0.10')
    self.assertEqual(
      configs[0]['targeting']['inventoryTargeting']['targetedPlacementIds'],
      [9876543, 1234567]
    )
    self.assertEqual(configs[0]['costPerUnit']['microAmount'], 100000)

    self.assertEqual(configs[2]['name'], 'Wonderful Ad Partner: HB $0.30')
    self.assertEqual(
      configs[2]['targeting']['inventoryTargeting']['targetedPlacementIds'],
      [9876543, 1234567]
    )
    self.assertEqual(configs[2]['costPerUnit']['microAmount'], 300000)
