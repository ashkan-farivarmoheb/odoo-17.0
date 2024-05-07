from odoo.exceptions import UserError
from odoo import models, fields, api, _, tools
from odoo import fields, models
import logging
import os
import base64
import shutil
import tarfile

_logger = logging.getLogger(__name__)


class StockPickingBatchAustraliaPost(models.Model):
    _inherit = "stock.picking.batch"
    order_id = fields.Char(string="Carrier Order Id", size=256)

    carrier_id = fields.Many2one('delivery.carrier',
                                 string="Delivery Method",
                                 copy=False,
                                 help="""According to the selected shipping provider,
                                 Visible the delivery method.""")

    ready_for_download = fields.Boolean('ReadyForDownload',
                                        default=False,
                                        copy=False,
                                        help="Mark as True when it's have tracking ref number.")

    def download_labels(self):
        """
        To download all labels for the picking from batch.
        @return: Zip file for all labels.
        """
        self.ensure_one()
        # Retrieve the Odoo data directory path from the configuration
        # Retrieve the base directory from the Odoo configuration
        data_dir = tools.config.get('data_dir')
        if not data_dir:
            raise ValueError(
                "The 'data_dir' configuration value is not set in Odoo.")

        # Define file path using the `data_dir`

        labels_dir = os.path.join(data_dir, "tmp", "labels")
        os.makedirs(labels_dir, exist_ok=True)

        file_path = f"{data_dir}/tmp/labels/"
        directory = os.path.dirname(file_path)

        # Filter pickings according to the specified criteria
        pickings = self.picking_ids.filtered(
            lambda x: x.picking_type_code in ('outgoing') and x.state in (
                'done') and x.carrier_id and x.carrier_tracking_ref)

        # Write label attachments to the directory
        for picking in pickings:
            tar_file_name = picking.name.replace('/', '_')
            label_attachments = self.env['ir.attachment'].search(
                [('res_model', '=', 'stock.picking'), ('res_id', '=', picking.id)])
            if not label_attachments:
                continue
            for sequence, label_attachment in enumerate(label_attachments, start=1):
                file_extension = label_attachment.name.split('.')[1] if \
                    label_attachment.name.split('.')[1] else "pdf"
                with open("%s%s_%s.%s" % (file_path, sequence, tar_file_name, file_extension),
                          "wb") as f:
                    f.write(base64.b64decode(
                        label_attachment and label_attachment.datas))

        # Create the tar.gz archive in <data_dir>/tmp/
        tar_file_name = "%s.tar.gz" % (self.name.replace(
            '/', '_') if self.name else 'Shipping_Labels')

        tar_path = os.path.join(data_dir, "tmp", tar_file_name)

        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(labels_dir, arcname="labels")

        # Log tar file creation
        _logger.debug(f"Created tar archive: {tar_path}")

        # Remove the labels directory after archiving
        shutil.rmtree(labels_dir)

        # Read and encode the tar.gz file
        with open(tar_path, "rb") as f1:
            file_data_temp = base64.b64encode(f1.read())
        _logger.debug(f"file_data_temp: {file_data_temp}")

        att_id = self.env['ir.attachment'].create({'name': "Wave -%s" % (tar_file_name or ""),
                                                   'store_fname': "Wave - %s.pdf" % (
                                                           tar_file_name or ""),
                                                   'type': 'binary',
                                                   'datas': file_data_temp or "",
                                                   'mimetype': 'application/pdf',
                                                   'res_model': 'stock.picking.batch',
                                                   'res_id': self.id, 'res_name': self.name})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?filename_field=name&download=true' % (att_id.id),
            'target': 'self'
        }

    def download_invoices(self):
        """
        To download invoices for all pickings in batch.
        @return: Zip file for all Invoices.
        """
        self.ensure_one()
        allow_partial_invoice = self.env['ir.config_parameter'].sudo().get_param(
            'batch_pickings_validate_ept.download_partial_invoice')
        invoice_ids = []
        invoice_messages = []
        not_allow_invoice = False
        for picking_id in self.picking_ids:
            if picking_id.sale_id and picking_id.sale_id.invoice_ids:
                for invoice_id in picking_id.sale_id.invoice_ids:
                    invoice_ids.append(invoice_id.id)
            else:
                not_allow_invoice = True
                invoice_messages.append("Invoice Is Not Created For This Order %s (%s)." % (
                    picking_id.origin, picking_id.name))
        if not invoice_ids:
            raise UserError(_("%s" % ('\n'.join(invoice_messages))))
        if not allow_partial_invoice and not_allow_invoice:
            raise UserError(_(
                "Invoice Is Not Available In Following Order\n %s" % (
                    '\n'.join(invoice_messages))))
        invoices = self.env['account.move'].search([('id', 'in', invoice_ids)])
        return self.env.ref('account.account_invoices').report_action(invoices)

    @api.depends('company_id', 'picking_type_id', 'state', 'carrier_id')
    def _compute_allowed_picking_ids(self):
        allowed_picking_states = ['waiting', 'confirmed', 'assigned']

        for batch in self:
            domain_states = list(allowed_picking_states)
            # Allows adding draft pickings only if the batch is in draft.
            if batch.state == 'draft':
                domain_states.append('draft')
            domain = [
                ('company_id', '=', batch.company_id.id),
                ('state', 'in', domain_states),
            ]
            if batch.picking_type_id:
                domain += [('picking_type_id', '=', batch.picking_type_id.id)]
            _logger.debug('allowed_pickings %s', domain)
            if self.carrier_id:
                allowed_picking_states += ['done']
                domain += [
                    ('picking_type_code', '=', 'outgoing'),
                    ('carrier_id', '!=', False),
                    ('carrier_id', '=', self.carrier_id.id),
                    ('send_to_shipper_process_done', '=', False),
                    ('carrier_tracking_ref', '=', False),
                    ('state', 'in', allowed_picking_states)
                ]

                _logger.debug('allowed_pickings filtered %s', domain)
            # Apply the existing domain logic
            allowed_pickings = self.env['stock.picking'].search(domain)
            _logger.debug('result self.carrier_id %s   allowed_pickings   %s',
                          self.carrier_id, allowed_pickings)
            # Apply additional filters

            batch.allowed_picking_ids = allowed_pickings
