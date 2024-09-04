/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.GlowingBlobEffect = publicWidget.Widget.extend({
    selector: '.glowing_blob_section',  // Target the section where the effect will be applied

    start: function () {
        this._super.apply(this, arguments);
        this._initBlobMovement();
        this._initTextEffect();
    },

    _initBlobMovement: function () {
        const blob = this.el.querySelector(".blob");  // Select the blob element

        window.onpointermove = (event) => {
            const {clientX, clientY} = event;  // Get the pointer coordinates

            // Animate the blob to follow the pointer movement
            blob.animate({
                left: `${clientX}px`,
                top: `${clientY}px`
            }, {duration: 3000, fill: "forwards"});
        };
    },

    _initTextEffect: function () {
        const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        let interval = null;

        this.el.querySelector("h1").onmouseover = (event) => {
            let iteration = 0;
            clearInterval(interval);  // Clear any existing interval

            interval = setInterval(() => {
                event.target.innerText = event.target.innerText
                    .split("")
                    .map((letter, index) => {
                        if (index < iteration) {
                            return event.target.dataset.value[index];
                        }
                        return letters[Math.floor(Math.random() * 26)];
                    })
                    .join("");

                if (iteration >= event.target.dataset.value.length) {
                    clearInterval(interval);  // Stop the effect once completed
                }

                iteration += 1 / 3;
            }, 30);  // Set interval speed for the text effect
        };
    }
});