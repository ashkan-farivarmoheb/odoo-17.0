/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MagicTextAEffect = publicWidget.Widget.extend({
    selector: '.magic', // The parent element that contains magic-star elements
    start: function () {
        this._super.apply(this, arguments);
        this._initAnimation();
    },

    _initAnimation: function () {
        let index = 0;
        const interval = 1000;

        // Random number generator
        const rand = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

        // Animate the stars
        const animate = (star) => {
            star.style.setProperty("--star-left", `${rand(-10, 100)}%`);
            star.style.setProperty("--star-top", `${rand(-40, 80)}%`);

            // Reset the animation
            star.style.animation = "none";
            star.offsetHeight;  // Trigger a reflow to restart the animation
            star.style.animation = "";
        };

        // Iterate over the magic-star elements
        for (const star of this.el.getElementsByClassName("magic-star")) {
            setTimeout(() => {
                animate(star);
                setInterval(() => animate(star), interval);
            }, index++ * (interval / 3));
        }
    }
});
