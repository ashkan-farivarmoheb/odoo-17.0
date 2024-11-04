/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.StickyImages = publicWidget.Widget.extend({
    selector: '.sticky_feature_img',

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this._initStickyImages();
        return this._super(...arguments);
    },

    /**
     * Initialize the sticky images functionality
     * @private
     */
    _initStickyImages: function () {
        // Store elements
        this.images = this.el.querySelectorAll('.sticky-image');
        this.sections = document.querySelectorAll('.text-section');

        if (this.images.length === 0 || this.sections.length === 0) {
            return;
        }

        // Initialize state
        this.currentImageIndex = 0;

        // Set initial states
        this.images.forEach((img, index) => {
            img.style.opacity = index === 0 ? '1' : '0';
            img.style.transition = 'opacity 0.3s ease-in-out';
        });

        // Initialize Intersection Observer
        this._initIntersectionObserver();
    },

    /**
     * Initialize Intersection Observer
     * @private
     */
    _initIntersectionObserver: function () {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const index = Array.from(this.sections).indexOf(entry.target);
                    this._updateImageForSection(index);
                }
            });
        }, {
            threshold: 0.5
        });

        this.sections.forEach(section => observer.observe(section));
    },

    /**
     * Update image for a specific section
     * @private
     */
    _updateImageForSection: function(index) {
        if (index !== this.currentImageIndex && index >= 0 && index < this.images.length) {
            this.images.forEach((img, i) => {
                img.style.opacity = i === index ? '1' : '0';
            });
            this.currentImageIndex = index;
        }
    },

    /**
     * @override
     */
    destroy: function () {
        this._super.apply(this, arguments);
    }
});