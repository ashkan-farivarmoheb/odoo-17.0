/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

// Parallax Effect Widget
publicWidget.registry.ParallaxEffect = animations.Animation.extend({
    selector: '.parallax-effect-parent-container',  // Apply to the parent container

    start: function () {
        console.log('ParallaxEffect widget started');
        this._super.apply(this, arguments);
        this.initParallaxEffect();
    },

    initParallaxEffect: function () {
        console.log('Initializing parallax effect');
        const self = this;

        this.$target.on('mousemove', '.card-hover', function (e) {
            const cardRect = this.getBoundingClientRect();
            const x = e.clientX - cardRect.left; // x position within the card
            const y = e.clientY - cardRect.top;  // y position within the card

            // Calculate the background position
            const moveX = ((x / cardRect.width) * 30) - 15; // Adjust range as needed
            const moveY = ((y / cardRect.height) * 30) - 15; // Adjust range as needed

            console.log(`Mousemove detected: x=${x}, y=${y}, moveX=${moveX}, moveY=${moveY}`); // Debugging mousemove

            // Apply the background position
            $(this).css('background-position', `${moveX}px ${moveY}px`);
        });

        this.$target.on('mouseleave', '.card-hover', function () {
            console.log('Mouse left the element, resetting background position');
            // Reset the background position when the mouse leaves the card
            $(this).css('background-position', 'center center');
        });
    },
});

// Hide On Hover Widget
publicWidget.registry.HideOnHover = animations.Animation.extend({
    selector: '.parallax-effect-parent-container',

    start: function () {
        console.log('HideOnHover widget started');
        this._super.apply(this, arguments);
        this.initHideOnHover();
    },

    initHideOnHover: function () {
        console.log('Initializing hide on hover');
        const self = this;

        // Hide the .hide-on-hover element and show the .card-hover element on mouse enter
        this.$target.on('mouseenter', function () {
            console.log('Mouse entered, hiding .hide-on-hover and showing .card-hover');
            self.$target.find('.hide-on-hover').css({
                'display': 'none',
            });
            self.$target.find('.card-hover').css({
                'display': 'block',
                'position': 'relative',
                'z-index': '10',
            });
        });

        // Reset the elements when the mouse leaves the parent container
        this.$target.on('mouseleave', function () {
            console.log('Mouse left, resetting elements');
            self.$target.find('.hide-on-hover').css({
                'display': 'block',
            });
            self.$target.find('.card-hover').css({
                'display': 'none',
            });
        });
    },
});

