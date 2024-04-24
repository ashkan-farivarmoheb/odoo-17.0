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
