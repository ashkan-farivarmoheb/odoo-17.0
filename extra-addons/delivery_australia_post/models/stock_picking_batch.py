import json

from .australia_post_repository import AustraliaPostRepository
from .australia_post_request import AustraliaPostRequest
from odoo.exceptions import UserError
from odoo import api, _, tools
from odoo import fields, models
import logging
import os
import base64
import shutil
import zipfile
from pathlib import Path

_logger = logging.getLogger(__name__)


class StockPickingBatchAustraliaPost(models.Model):
    _inherit = "stock.picking.batch"
    order_id = fields.Char(string="Carrier Order Id", size=256)

    carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Delivery Method",
        copy=False,
        help="""According to the selected shipping provider,
                                 Visible the delivery method.""",
    )

    ready_for_download = fields.Boolean(
        "ReadyForDownload",
        default=False,
        copy=False,
        help="Mark as True when it's have tracking ref number.",
    )

    _australia_post_request_instance = None
    _australia_post_repository_instance = None

    @classmethod
    def _get_australia_post_request(cls):
        """Retrieve or create an instance of AustraliaPostRequest with order and carrier details."""
        if cls._australia_post_request_instance is None:
            cls._australia_post_request_instance = AustraliaPostRequest.get_instance()
        return cls._australia_post_request_instance

    @classmethod
    def _get_australia_post_repository(cls):
        if cls._australia_post_repository_instance is None:
            cls._australia_post_repository_instance = (
                AustraliaPostRepository.get_instance()
            )
        return cls._australia_post_repository_instance

    def download_invoices(self):
        """
        To download invoices for all pickings in batch.
        @return: Zip file for all Invoices.
        """
        self.ensure_one()
        allow_partial_invoice = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("batch_pickings_validate_ept.download_partial_invoice")
        )
        invoice_ids = []
        invoice_messages = []
        not_allow_invoice = False
        for picking_id in self.picking_ids:
            if picking_id.sale_id and picking_id.sale_id.invoice_ids:
                for invoice_id in picking_id.sale_id.invoice_ids:
                    invoice_ids.append(invoice_id.id)
            else:
                not_allow_invoice = True
                invoice_messages.append(
                    "Invoice Is Not Created For This Order %s (%s)."
                    % (picking_id.origin, picking_id.name)
                )
        if not invoice_ids:
            raise UserError(_("%s" % ("\n".join(invoice_messages))))
        if not allow_partial_invoice and not_allow_invoice:
            raise UserError(
                _(
                    "Invoice Is Not Available In Following Order\n %s"
                    % ("\n".join(invoice_messages))
                )
            )
        invoices = self.env["account.move"].search([("id", "in", invoice_ids)])
        return self.env.ref("account.account_invoices").report_action(invoices)

    def download_labels(self):
        """
        Package all labels for the pickings in the batch into a ZIP file.
        @return: ZIP file containing all labels.
        """
        self.ensure_one()
        # Retrieve the Odoo data directory path from the configuration
        data_dir = tools.config.get("data_dir")
        if not data_dir:
            raise ValueError(
                "The 'data_dir' configuration value is not set in Odoo.")

        # Define file path using the `data_dir`
        labels_dir = Path(data_dir, "tmp", "labels")
        labels_dir.mkdir(parents=True, exist_ok=True)
        # Filter pickings with labels
        pickings = self.picking_ids.filtered(
            lambda x: x.picking_type_code == "outgoing"
                      and x.state == "done"
                      and x.carrier_id
                      and x.shipment_id
        )

        if not pickings:
            raise UserError(_("No pickings found with labels to download."))

        requests = self._get_australia_post_request().create_post_labels_batch_request(pickings)
        responses = [
            self._get_australia_post_repository().create_labels(carrier.read()[0], request)
            for carrier, requests in requests.items() for request in requests]

        # Create the ZIP archive in <data_dir>/tmp/
        zip_dir = Path(data_dir, "tmp", "label_zip")
        zip_dir.mkdir(parents=True, exist_ok=True)

        zip_file_name = "%s.zip" % (
            self.name.replace("/", "_") if self.name else "Shipping_Labels"
        )
        zip_path = zip_dir / zip_file_name
        _logger.debug("zip_path %s zip_file_name %s file_path %s labels_dir %s",
                      zip_path, zip_file_name, labels_dir, labels_dir)

        try:

            with zipfile.ZipFile(zip_path, "w") as zipf:
                label_attachments = self.env["ir.attachment"].search(
                    [
                        ("res_model", "=", "stock.picking.batch"),
                        ("res_id", "=", self.id),
                        ("mimetype", "=", "application/pdf"),
                    ]
                )
                _logger.debug("label_attachment for %s", self)

                for response in responses:
                    label_attachments = self.env["ir.attachment"].search(
                        [
                            ("res_model", "=", "stock.picking.batch"),
                            ("res_id", "=", self.id),
                            ("mimetype", "=", "application/pdf"),
                        ]
                    )
                    _logger.debug("label_attachment for %s", self)
                    if not label_attachments:
                        _logger.debug("no label_attachment for %s", self)
                        report_data = self.stock_picking_action_report(picking)
                        if report_data:
                            label_attachments = report_data
                        else:
                            continue

                    for sequence, label_attachment in enumerate(
                        label_attachments, start=1
                    ):
                        if isinstance(label_attachment, dict):
                            pdf_content = base64.b64decode(
                                label_attachment.get('datas'))
                            file_extension = (
                                label_attachment.get('name').split(".")[1]
                                if label_attachment.get('name').split(".")[1]
                                else "pdf"
                            )
                        else:
                            pdf_content = base64.b64decode(
                                label_attachment.datas)
                            file_extension = (
                                label_attachment.name.split(".")[1]
                                if label_attachment.name.split(".")[1]
                                else "pdf"
                            )
                        # Construct the PDF filename and path
                        pdf_filename = "%s_%s.%s" % (
                            sequence,
                            picking.name.replace("/", "_"),
                            file_extension,
                        )
                        pdf_path = labels_dir / pdf_filename
                        _logger.debug(
                            f"PDF path for {picking.name}: {pdf_path}")
                        # Write the PDF content to a file in data_dir
                        with open(pdf_path, "wb") as f:
                            f.write(pdf_content)
                        # Add the PDF file to the ZIP file
                        zipf.write(pdf_path, pdf_filename)
                        # Remove the PDF file after adding it to the ZIP
                        os.remove(pdf_path)

            # Read and encode the ZIP file
            with open(zip_path, "rb") as f:
                zip_data = base64.b64encode(f.read())
            _logger.debug(f"zip_data: {zip_data}")

            # Create an attachment for the ZIP file
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "Wave - %s.zip" % (zip_file_name or ""),
                    "store_fname": "Wave - %s.zip" % (zip_file_name or ""),
                    "type": "binary",
                    "datas": zip_data or "",
                    "mimetype": "application/zip",
                    "res_model": "stock.picking.batch",
                    "res_id": self.id,
                    "res_name": self.name,
                }
            )

            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/%s?filename_field=name&download=true"
                       % (attachment.id),
                "target": "self",
            }
        finally:
            msg = _(
                "Delivery slip ZIP files have been created and downloaded for Batch Transfer %s. To see the tracking numbers, check the ZIP file or the stock picking/package.") % (
                      self.name)
            self.message_post(
                body=msg,
                subject="Attachments of tracking",
            )

            # Cleanup the ZIP file after download
            if os.path.exists(zip_path):
                os.remove(zip_path)
            # Cleanup the pdf file
            if os.path.exists(pdf_path):
                shutil.rmtree(pdf_path)

        # try:
        #
        #     with zipfile.ZipFile(zip_path, "w") as zipf:
        #         for picking in pickings:
        #             label_attachments = self.env["ir.attachment"].search(
        #                 [
        #                     ("res_model", "=", "stock.picking"),
        #                     ("res_id", "=", picking.id),
        #                     ("mimetype", "=", "application/pdf"),
        #                 ]
        #             )
        #             _logger.debug("label_attachment for %s", picking)
        #             if not label_attachments:
        #                 _logger.debug("no label_attachment for %s", picking)
        #                 report_data = self.stock_picking_action_report(picking)
        #                 if report_data:
        #                     label_attachments = report_data
        #                 else:
        #                     continue
        #
        #             for sequence, label_attachment in enumerate(
        #                 label_attachments, start=1
        #             ):
        #                 if isinstance(label_attachment, dict):
        #                     pdf_content = base64.b64decode(
        #                         label_attachment.get('datas'))
        #                     file_extension = (
        #                         label_attachment.get('name').split(".")[1]
        #                         if label_attachment.get('name').split(".")[1]
        #                         else "pdf"
        #                     )
        #                 else:
        #                     pdf_content = base64.b64decode(
        #                         label_attachment.datas)
        #                     file_extension = (
        #                         label_attachment.name.split(".")[1]
        #                         if label_attachment.name.split(".")[1]
        #                         else "pdf"
        #                     )
        #                 # Construct the PDF filename and path
        #                 pdf_filename = "%s_%s.%s" % (
        #                     sequence,
        #                     picking.name.replace("/", "_"),
        #                     file_extension,
        #                 )
        #                 pdf_path = labels_dir / pdf_filename
        #                 _logger.debug(
        #                     f"PDF path for {picking.name}: {pdf_path}")
        #                 # Write the PDF content to a file in data_dir
        #                 with open(pdf_path, "wb") as f:
        #                     f.write(pdf_content)
        #                 # Add the PDF file to the ZIP file
        #                 zipf.write(pdf_path, pdf_filename)
        #                 # Remove the PDF file after adding it to the ZIP
        #                 os.remove(pdf_path)
        #
        #     # Read and encode the ZIP file
        #     with open(zip_path, "rb") as f:
        #         zip_data = base64.b64encode(f.read())
        #     _logger.debug(f"zip_data: {zip_data}")
        #
        #     # Create an attachment for the ZIP file
        #     attachment = self.env["ir.attachment"].create(
        #         {
        #             "name": "Wave - %s.zip" % (zip_file_name or ""),
        #             "store_fname": "Wave - %s.zip" % (zip_file_name or ""),
        #             "type": "binary",
        #             "datas": zip_data or "",
        #             "mimetype": "application/zip",
        #             "res_model": "stock.picking.batch",
        #             "res_id": self.id,
        #             "res_name": self.name,
        #         }
        #     )
        #
        #     return {
        #         "type": "ir.actions.act_url",
        #         "url": "/web/content/%s?filename_field=name&download=true"
        #                % (attachment.id),
        #         "target": "self",
        #     }
        # finally:
        #     msg = _(
        #         "Delivery slip ZIP files have been created and downloaded for Batch Transfer %s. To see the tracking numbers, check the ZIP file or the stock picking/package.") % (
        #               self.name)
        #     self.message_post(
        #         body=msg,
        #         subject="Attachments of tracking",
        #     )
        #
        #     # Cleanup the ZIP file after download
        #     if os.path.exists(zip_path):
        #         os.remove(zip_path)
        #     # Cleanup the pdf file
        #     if os.path.exists(pdf_path):
        #         shutil.rmtree(pdf_path)

    @api.depends("company_id", "picking_type_id", "state", "carrier_id")
    def _compute_allowed_picking_ids(self):
        allowed_picking_states = ["waiting", "confirmed", "assigned"]

        for batch in self:
            domain_states = list(allowed_picking_states)
            # Allows adding draft pickings only if the batch is in draft.
            if batch.state == "draft":
                domain_states.append("draft")
            domain = [
                ("company_id", "=", batch.company_id.id),
                ("state", "in", domain_states),
            ]
            if batch.picking_type_id:
                domain += [("picking_type_id", "=", batch.picking_type_id.id)]
            _logger.debug("allowed_pickings %s", domain)
            if self.carrier_id:
                allowed_picking_states += ["done"]
                domain += [
                    ("picking_type_code", "=", "outgoing"),
                    ("carrier_id", "!=", False),
                    ("carrier_id", "=", self.carrier_id.id),
                    ("send_to_shipper_process_done", "=", False),
                    ("carrier_tracking_ref", "=", False),
                    ("state", "in", allowed_picking_states),
                ]

            # Apply the existing domain logic
            allowed_pickings = self.env['stock.picking'].search(domain)

            # Apply additional filters

            batch.allowed_picking_ids = allowed_pickings

    def stock_picking_action_report(self, picking):
        """
        Call a specific report action on the stock.picking model.
        @param picking: stock.picking record to call the action on.
        @return: Report data
        """
        report = self.env['ir.actions.report']._render_qweb_pdf(
            "stock.action_report_delivery", picking.id)

        if not report:
            _logger.error(
                "Report action with ID 'stock.action_report_picking' not found.")
            raise UserError(
                _("Report action with ID 'stock.action_report_picking' not found."))

        pdf = report[0]
        label_attachment = {
            'datas': base64.b64encode(pdf).decode('utf-8'),
            'name': 'picking_report_%s.pdf' % picking.name.replace("/", "_")
        }

        return [label_attachment]

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        if self.carrier_id.delivery_type == 'auspost':
            outgoing_picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
            if outgoing_picking_type:
                self.picking_type_id = outgoing_picking_type
            else:
                self.carrier_id = False

    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):
        if self.carrier_id.delivery_type == 'auspost' and self.picking_type_code != 'outgoing':
            self.carrier_id = False
