/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ExpandableCards = publicWidget.Widget.extend({
    selector: '.expandable_cards',
    events: {
        'click .expandable_card': '_onCardClick', // Register click event for cards
    },

    _onCardClick: function (ev) {
        const $card = $(ev.currentTarget);
        $card.toggleClass('expanded'); // Toggle the 'expanded' class on click
    }
});
