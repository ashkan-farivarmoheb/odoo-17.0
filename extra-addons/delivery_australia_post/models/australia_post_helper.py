import logging
from PyPDF2 import PdfMerger
from odoo.exceptions import ValidationError
from odoo import _
from pathlib import Path
import os
import base64
import zipfile
import requests
from odoo.http import request


class AustraliaPostHelper:

    @staticmethod
    def append_pdfs(pdf_dir, pdf_file_name, files_to_append):
        """
        Append PDF files into a single PDF file.
        :param pdf_dir: Directory where the combined PDF file will be created.
        :param pdf_file_name: Name of the combined PDF file.
        :param files_to_append: List of file paths to append into the combined PDF.
        :return: Path to the created combined PDF file.
        """
        pdf_path = pdf_dir / pdf_file_name
        merger = PdfMerger()

        for file_path in files_to_append:
            if os.path.exists(file_path):
                merger.append(file_path)

        merger.write(pdf_path)
        merger.close()
        return pdf_path


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
            if not picking.carrier_id:
                raise ValidationError(_("no Carrier provided"))
            carrier_id = picking.carrier_id
            authority_to_leave, allow_partial_delivery = AustraliaPostHelper._determine_authority_and_delivery(
                package, carrier_id)
            shipping_weight = AustraliaPostHelper._compute_api_weight(
                carrier_id, package.shipping_weight)
            item = {
                "item_reference": package.name,
                "product_id": picking.carrier_id.service_product_id,
                'length': round(package.length, 1),
                'width':  round(package.width, 1),
                'height':  round(package.height, 1),
                'weight': round(shipping_weight, 3),
                "authority_to_leave": authority_to_leave,
                "allow_partial_delivery": allow_partial_delivery,
                "safe_drop_enabled": True
                # / https://developers.auspost.com.au/content/downloads/AP_ATL_Shipping_and_TrackingFactSheet_FA.pdf
            }
            items.append(item)
        return items

    @staticmethod
    def map_rate_shipment_items(carrier, order):
        _logger.debug('Preparing product details for order: %s', order.name)
        if not carrier.service_product_id:
            raise ValidationError(_("no Carrier provided"))
        service_product_id = carrier.service_product_id
        shipping_weight = AustraliaPostHelper._compute_api_weight(
            carrier, order.shipping_weight)
        # TODO order L W H for rate request?
        return [{
            'length': "5",
            'width': "10",
            'height': "1",
            'weight': round(shipping_weight, 3),
            'item_reference': order.name,
            'product_ids': [service_product_id]
        }]

    @staticmethod
    def _compute_api_weight(carrier, shipping_weight):
        api_weight = carrier._get_api_weight(
            shipping_weight)
        _logger.debug(
            "converted to api_weight %s", api_weight)
        return api_weight

    @staticmethod
    def _determine_authority_and_delivery(package, carrier):
        if carrier:
            authority_to_leave = package.authority_leave if package.authority_leave is not None else carrier.authority_leave
            allow_partial_delivery = package.allow_part_delivery if package.allow_part_delivery is not None else carrier.allow_part_delivery
        else:
            authority_to_leave = False
            allow_partial_delivery = False

        return authority_to_leave, allow_partial_delivery

    @staticmethod
    def create_zip(zip_dir, zip_file_name, files_to_zip):
        """
        Create a ZIP file containing the specified files.
        :param zip_dir: Directory where the ZIP file will be created.
        :param zip_file_name: Name of the ZIP file.
        :param files_to_zip: List of file paths to include in the ZIP file.
        :return: Path to the created ZIP file.
        """
        zip_path = zip_dir / zip_file_name
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for file_path in files_to_zip:
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
        return zip_path

    @staticmethod
    def combine_pdfs(pdf_dir, pdf_file_name, files_to_append):
        """
        Append PDF files into a single PDF file.
        :param pdf_dir: Directory where the combined PDF file will be created.
        :param pdf_file_name: Name of the combined PDF file.
        :param files_to_append: List of file paths to append into the combined PDF.
        :return: Path to the created combined PDF file.
        """
        pdf_path = pdf_dir / pdf_file_name
        merger = PdfMerger()

        for file_path in files_to_append:
            if os.path.exists(file_path):
                merger.append(file_path)

        merger.write(pdf_path)
        merger.close()
        return pdf_path

    @staticmethod
    def map_pickings_to_preferences(carrier):
        return {
            "type": "PRINT",
            "format": "ZPL",
            "metadata": {
                "group": carrier.service_group,
                "branded": carrier.branded,
                "layout": carrier.label_layout_type if carrier.label_layout_type else "A4-1pp",
                "left_offset": carrier.left_offset,
                "top_offset": carrier.top_offset
            }
        }

    @staticmethod
    def create_pdf_with_path(labels_dir, report_data, name, seq):
        pdf_filename = "%s_%s.%s" % (
            seq,
            name.replace("/", "_"),
            'pdf',
        )
        pdf_path = labels_dir / pdf_filename
        pdf_content = base64.b64decode(report_data[0])
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)
        return pdf_filename, pdf_path

    @staticmethod
    def label_action_report(label_response):
        if len(label_response.get('data').get('labels')) > 0:
            url = label_response.get('data').get('labels')[0].get('url')

        try:
            response = requests.get(url)
            response.raise_for_status()
            return [base64.b64encode(response.content).decode('utf-8')]

        except requests.RequestException as e:
            return request.not_found()

    @staticmethod
    def create_zipfile_with_path(data_dir, labels_dir, name):
        zip_dir = Path(data_dir, "tmp", "label_zip")
        zip_dir.mkdir(parents=True, exist_ok=True)
        zip_file_name = "%s" % (
            name.replace("/", "_") if name else "Shipping_Labels"
        )
        zip_path = zip_dir / zip_file_name
        _logger.debug("zip_path %s zip_file_name %s file_path %s labels_dir %s",
                      zip_path, zip_file_name, labels_dir, labels_dir)
        return zip_file_name, zip_path
