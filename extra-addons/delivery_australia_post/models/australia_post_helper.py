import logging


_logger = logging.getLogger(__name__)


class AustraliaPostHelper(object):
    @staticmethod
    def map_to_wizard_info(account_info):
        return {
            'name': account_info['name'],
            'valid_from': account_info['valid_from'],
            'valid_to': account_info['valid_to'],
            'account_number': account_info['account_number'],
            'expired':  account_info['expired'],
            'merchant_location_id': account_info['merchant_location_id'],
            'credit_blocked': account_info['credit_blocked']
        }

    @staticmethod
    def map_to_wizard_line(postage_product, wizard_id, carrier_id):
        return {
            'carrier': carrier_id,
            'type': postage_product['type'],
            'group': postage_product['group'],
            'product_id': postage_product['product_id'],
            'wizard_id': wizard_id
        }

    @staticmethod
    def map_to_wizard_lines(postage_products, wizard_id, carrier_id):
        return list(map(AustraliaPostHelper.map_to_wizard_line, postage_products,
                        [wizard_id] * len(postage_products), [carrier_id] * len(postage_products)))

    @staticmethod
    def map_res_partner_to_shipment(res_partner):
        return {
            'name': res_partner.name,
            'lines': [res_partner.street or '', res_partner.street2 or ''],
            'suburb': res_partner.city,
            'state': res_partner.state_id.name if res_partner.state_id else '',
            'postcode': res_partner.zip,
            'phone': res_partner.phone,
            'email': res_partner.email
        }

    @staticmethod
    def map_shipment_items(picking):
        items = []
        _logger.debug(
            "map_shipment_items picking.package_ids: %s", picking.package_ids)

        for package in picking.package_ids:
            carrier = getattr(picking, 'carrier_id', None)
            authority_to_leave, allow_partial_delivery = AustraliaPostHelper.determine_authority_and_delivery(
                package, carrier)

            item = {
                "item_reference": package.name,
                "product_id": picking.carrier_id.service_product_id,
                'length': package.length,
                'width':  package.width,
                'height':  package.height,
                'weight': package.weight,
                "authority_to_leave": authority_to_leave,
                "allow_partial_delivery": allow_partial_delivery,
                "safe_drop_enabled": True
                # / https://developers.auspost.com.au/content/downloads/AP_ATL_Shipping_and_TrackingFactSheet_FA.pdf
            }
            items.append(item)
        return items

    @staticmethod
    def determine_authority_and_delivery(package, carrier):
        if carrier:
            authority_to_leave = package.authority_leave if package.authority_leave is not None else carrier.authority_leave
            allow_partial_delivery = package.allow_part_delivery if package.allow_part_delivery is not None else carrier.allow_part_delivery
        else:
            authority_to_leave = False
            allow_partial_delivery = False

        return authority_to_leave, allow_partial_delivery

    @staticmethod
    def map_pickings_to_preferences(carrier):
        return {
            "type": "PRINT",
            "format": "ZPL",
            "metadata": {
                "group": carrier.service_group,
                "branded": carrier.branded,
                "layout": "A4-4pp",
                "left_offset": 0,
                "top_offset": 0
            }
        }
