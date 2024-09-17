/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MagicalHoverCardEffect = publicWidget.Widget.extend({
    selector: '.magical_hover_cards',
    events: {
        'mousemove': '_onMouseMove',
    },

    _onMouseMove: function (e) {
        const cards = this.el.getElementsByClassName("magical_hover_card");

        for (const card of cards) {
            const rect = card.getBoundingClientRect(),
                x = e.clientX - rect.left,
                y = e.clientY - rect.top;

            card.style.setProperty("--mouse-x", `${x}px`);
            card.style.setProperty("--mouse-y", `${y}px`);


        }
    }
});
