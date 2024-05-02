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
        for move in picking.move_ids:
            item = {
                "item_reference": move.product_id.product_tmpl_id.name,
                "product_id": picking.carrier_id.service_product_id,
                'length': "5",
                'width': "10",
                'height': "1",
                'weight': move.weight,
                "authority_to_leave": picking.carrier_id.authority_leave if picking.carrier_id else False,
                "allow_partial_delivery": picking.carrier_id.allow_part_delivery if picking.carrier_id else False,
            }
            items.append(item)
        return items

