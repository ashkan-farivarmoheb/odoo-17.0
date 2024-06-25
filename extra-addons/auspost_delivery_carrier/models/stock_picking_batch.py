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
from .australia_post_helper import AustraliaPostHelper

_logger = logging.getLogger(__name__)

data_dir = tools.config.get("data_dir")


class StockPickingBatchAustraliaPost(models.Model):
    _inherit = "stock.picking.batch"
    order_id = fields.Char(string="Carrier Order Id", size=256)
    DOWNLOAD_LABEL_MESSAGE = ("Delivery label ZIP files have been created and downloaded for Batch Transfer %s. To see "
                              "the tracking numbers, check the ZIP file or the stock picking/package.")
    DOWNLOAD_SLIP_MESSAGE = ("Delivery slip ZIP files have been created and downloaded for Batch Transfer %s. To see "
                             "the tracking numbers, check the ZIP file or the stock picking/package.")

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
            outgoing_picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'outgoing')], limit=1)
            if outgoing_picking_type:
                self.picking_type_id = outgoing_picking_type
            else:
                self.carrier_id = False

    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):
        if self.carrier_id.delivery_type == 'auspost' and self.picking_type_code != 'outgoing':
            self.carrier_id = False

    def download_delivery_slip_zip(self):
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

        # Define file path for temporary labels storage using the `data_dir`
        labels_dir = Path(data_dir, "tmp", "labels")
        labels_dir.mkdir(parents=True, exist_ok=True)

        # Filter pickings with labels that are outgoing and done
        pickings = self.picking_ids.filtered(
            lambda x: x.picking_type_code == "outgoing"
                      and x.state == "done"
                      and x.carrier_id
                      and x.carrier_tracking_ref
        ).sorted(key=lambda x: x.id)

        # Raise an error if no pickings are found
        if not pickings:
            raise UserError(_("No pickings found with labels to download."))

        files_to_zip = []

        # Iterate through each picking to gather label attachments
        for picking in pickings:
            label_attachments = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "stock.picking"),
                    ("res_id", "=", picking.id),
                    ("mimetype", "=", "application/pdf"),
                ]

            )
            _logger.debug("label_attachment for %s", picking)

            # If no label attachments found, generate report data
            if not label_attachments:
                _logger.debug("no label_attachment for %s", picking)
                report_data = self.stock_picking_action_report(picking)
                if report_data:
                    label_attachments = report_data
                else:
                    continue

            # Process each label attachment
            for sequence, label_attachment in enumerate(label_attachments, start=1):
                if isinstance(label_attachment, dict):
                    pdf_content = base64.b64decode(
                        label_attachment.get('datas'))
                    file_extension = label_attachment.get('name').split(".")[1] if len(
                        label_attachment.get('name').split(".")) > 1 else "pdf"
                else:
                    pdf_content = base64.b64decode(label_attachment.datas)
                    file_extension = label_attachment.name.split(".")[1] if len(
                        label_attachment.name.split(".")) > 1 else "pdf"

                # Construct the PDF filename and path
                pdf_filename = "%s_%s.%s" % (
                    sequence,
                    picking.name.replace("/", "_"),
                    file_extension,
                )
                pdf_path = labels_dir / pdf_filename
                _logger.debug(f"PDF path for {picking.name}: {pdf_path}")

                # Write the PDF content to a file in the data directory
                with open(pdf_path, "wb") as f:
                    f.write(pdf_content)

                # Add the file path to the list of files to be zipped
                files_to_zip.append(pdf_path)

        # Define file path for the ZIP archive in <data_dir>/tmp/
        zip_dir = Path(data_dir, "tmp", "label_zip")
        zip_dir.mkdir(parents=True, exist_ok=True)

        # Define the name of the ZIP file
        zip_file_name = "%s.zip" % (
            self.name.replace("/", "_") if self.name else "Shipping_Labels"
        )

        # Create the ZIP file with the gathered label files
        zip_path = AustraliaPostHelper.create_zip(
            zip_dir, zip_file_name, files_to_zip)

        try:
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
            # Get the URL for the attachment to allow downloading the ZIP file
            download_url = "/web/content/%s?filename_field=name&download=true" % attachment.id

            # Return the action to download the ZIP file
            return {
                "type": "ir.actions.act_url",
                "url": download_url,
                "target": "self",
            }
        finally:
            msg = _(StockPickingBatchAustraliaPost.DOWNLOAD_SLIP_MESSAGE) % (self.name)
            self.message_post(body=msg, subject="Attachments of tracking")

            # TODO Remove the combined PDF file from the attachment model  after ensuring the download is complete. This might involve a callback or a scheduled job
            # if attachment:
            #     attachment.unlink()
            # Remove the ZIP file after download
            if os.path.exists(zip_path):
                os.remove(zip_path)

            # Remove temporary PDF files
            for file_path in files_to_zip:
                if os.path.exists(file_path):
                    os.remove(file_path)

    def download_labels(self):
        """
        Package all labels for the pickings in the batch into a ZIP file.
        @return: ZIP file containing all labels.
        """
        self.ensure_one()
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
                      and x.carrier_id.delivery_type == "auspost"
                      and x.shipment_id
        )

        if not pickings:
            raise UserError(_("No pickings found with labels to download."))

        requests = self._get_australia_post_request().create_post_labels_batch_request(pickings)
        responses = [
            self._get_australia_post_repository().create_labels(carrier.read()[0], request)
            for carrier, requests in requests.items() for request in requests]

        zip_file_name, zip_path = AustraliaPostHelper.create_zipfile_with_path(data_dir, labels_dir, self.name)
        pdf_paths = []

        try:
            with zipfile.ZipFile(zip_path, "w") as zipf:
                seq = 0
                for response in responses:
                    seq += 1
                    report_data = AustraliaPostHelper.label_action_report(response)
                    if report_data:
                        pdf_filename, pdf_path = AustraliaPostHelper.create_pdf_with_path(labels_dir, report_data,
                                                                                          self.name, seq)
                        # Add the PDF file to the ZIP file
                        zipf.write(pdf_path, pdf_filename)
                        # Remove the PDF file after adding it to the ZIP
                        os.remove(pdf_path)

            attachment = self._create_zipfile_attachment(zip_file_name, zip_path)

            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/%s?filename_field=name&download=true"
                       % (attachment.id),
                "target": "self",
            }
        finally:
            msg = _(StockPickingBatchAustraliaPost.DOWNLOAD_LABEL_MESSAGE) % (self.name)
            self.message_post(body=msg, subject="Attachments of tracking")

            # Cleanup the ZIP file after download
            if os.path.exists(zip_path):
                os.remove(zip_path)
            # Cleanup the pdf file
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

    def download_delivery_slip(self):
        """
        Package all labels for the pickings in the batch into a combined PDF file.
        @return: URL to download the combined PDF file containing all labels.
        """
        self.ensure_one()
        if not data_dir:
            raise ValueError(
                "The 'data_dir' configuration value is not set in Odoo.")

        # Define file path for temporary labels storage using the `data_dir`
        labels_dir = Path(data_dir, "tmp", "labels")
        labels_dir.mkdir(parents=True, exist_ok=True)

        # Filter pickings with labels that are outgoing and done
        pickings = self.picking_ids.filtered(
            lambda x: x.picking_type_code == "outgoing"
                      and x.state == "done"
                      and x.carrier_id
                      and x.carrier_tracking_ref
        ).sorted(key=lambda x: x.id)

        # Raise an error if no pickings are found
        if not pickings:
            raise UserError(_("No pickings found with labels to download."))

        files_to_append = []

        # Iterate through each picking to gather label attachments
        for picking in pickings:
            label_attachments = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "stock.picking"),
                    ("res_id", "=", picking.id),
                    ("mimetype", "=", "application/pdf"),
                ]
            )
            _logger.debug("label_attachment for %s", picking)

            # If no label attachments found, generate report data
            if not label_attachments:
                _logger.debug("no label_attachment for %s", picking)
                report_data = self.stock_picking_action_report(picking)
                if report_data:
                    label_attachments = report_data
                else:
                    continue

            # Process each label attachment
            for sequence, label_attachment in enumerate(label_attachments, start=1):
                if isinstance(label_attachment, dict):
                    pdf_content = base64.b64decode(
                        label_attachment.get('datas'))
                    file_extension = label_attachment.get('name').split(".")[1] if len(
                        label_attachment.get('name').split(".")) > 1 else "pdf"
                else:
                    pdf_content = base64.b64decode(label_attachment.datas)
                    file_extension = label_attachment.name.split(".")[1] if len(
                        label_attachment.name.split(".")) > 1 else "pdf"

                # Construct the PDF filename and path
                pdf_filename = "%s_%s.%s" % (
                    sequence,
                    picking.name.replace("/", "_"),
                    file_extension,
                )
                pdf_path = labels_dir / pdf_filename
                _logger.debug(f"PDF path for {picking.name}: {pdf_path}")

                # Write the PDF content to a file in the data directory
                with open(pdf_path, "wb") as f:
                    f.write(pdf_content)

                # Add the file path to the list of files to be appended
                files_to_append.append(pdf_path)

        # Define file path for the combined PDF file in <data_dir>/tmp/
        pdf_dir = Path(data_dir, "tmp", "combined_pdfs")
        pdf_dir.mkdir(parents=True, exist_ok=True)

        # Define the name of the combined PDF file
        pdf_file_name = "%s.pdf" % (
            self.name.replace("/", "_") if self.name else "Shipping_Labels"
        )

        # Create the combined PDF file with the gathered label files
        combined_pdf_path = AustraliaPostHelper.combine_pdfs(
            pdf_dir, pdf_file_name, files_to_append)

        try:
            # Read and encode the combined PDF file
            with open(combined_pdf_path, "rb") as f:
                pdf_data = base64.b64encode(f.read())
            _logger.debug(f"pdf_data: {pdf_data}")

            # Create an attachment for the combined PDF file
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "Wave - %s.pdf" % (pdf_file_name or ""),
                    "store_fname": "Wave - %s.pdf" % (pdf_file_name or ""),
                    "type": "binary",
                    "datas": pdf_data or "",
                    "mimetype": "application/pdf",
                    "res_model": "stock.picking.batch",
                    "res_id": self.id,
                    "res_name": self.name,
                }
            )

            # Get the URL for the attachment to allow downloading the combined PDF file
            download_url = "/web/content/%s?filename_field=name&download=true" % attachment.id

            # Return the URL for downloading the combined PDF file
            return {
                "type": "ir.actions.act_url",
                "url": download_url,
                "target": "self",
            }
        finally:
            # Log a message about the download
            msg = _(
                "Delivery slip PDF files have been created and downloaded for Batch Transfer %s. To see the tracking numbers, check the PDF file or the stock picking/package.") % (
                      self.name)
            self.message_post(
                body=msg,
                subject="Attachments of tracking",
            )

            # TODO Remove the combined PDF file from the attachment model  after ensuring the download is complete. This might involve a callback or a scheduled job
            # if attachment:
            #     attachment.unlink()

            # Remove the combined PDF file after use to save storage
            if os.path.exists(combined_pdf_path):
                os.remove(combined_pdf_path)

            # Remove temporary PDF files
            for file_path in files_to_append:
                if os.path.exists(file_path):
                    os.remove(file_path)

    def _create_zipfile_attachment(self, zip_file_name, zip_path):
        # Read and encode the ZIP file
        with open(zip_path, "rb") as f:
            zip_data = base64.b64encode(f.read())
        # Create an attachment for the ZIP file
        return self.env["ir.attachment"].create(
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
