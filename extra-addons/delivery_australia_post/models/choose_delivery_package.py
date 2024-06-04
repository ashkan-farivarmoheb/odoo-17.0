from odoo import fields, models, api, _


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"
    authority_leave = fields.Boolean(
        string="Authority to Leave",
        help="Allow delivery without recipient signature.",
        compute='_compute_authority_leave',
        store=True,
        readonly=False
    )

    allow_part_delivery = fields.Boolean(
        string="Allow Partial Delivery",
        help="Permit the delivery of orders in multiple shipments.",
        compute='_compute_allow_part_delivery',
        store=True,
        readonly=False
    )

    @api.depends('picking_id.carrier_id')
    def _compute_allow_part_delivery(pack):
        for pack in pack:
            if not pack.allow_part_delivery:
                if pack.picking_id.carrier_id:
                    pack.allow_part_delivery = pack.picking_id.carrier_id.allow_part_delivery
                else:
                    pack.allow_part_delivery = False

    @api.depends('picking_id.carrier_id')
    def _compute_authority_leave(self):
        for pack in self:
            if not pack.authority_leave:
                if pack.picking_id.carrier_id:
                    pack.authority_leave = pack.picking_id.carrier_id.authority_leave
                else:
                    pack.authority_leave = False

    def action_put_in_pack(self):
        ctx = dict(self._context)
        ctx['default_authority_leave'] = self.authority_leave
        ctx['default_allow_part_delivery'] = self.allow_part_delivery

        # Call the partent method with the updated context
        super(ChooseDeliveryPackage,
              self.with_context(ctx)).action_put_in_pack()
