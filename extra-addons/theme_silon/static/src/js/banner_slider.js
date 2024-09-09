/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.BannerSlider = publicWidget.Widget.extend({
    selector: '.banner_slider_section .carousel',
    events: {
        'click #next': '_onClickNext',
        'click #prev': '_onClickPrev',
        'click .thumbnail .item': '_onClickThumbnail', // Add click event for thumbnails
    },

    start: function () {
        this.timeRunning = 3000;
        this.timeAutoNext = 7000;
        this.runTimeOut = null;
        this.runNextAuto = null;

        // Store DOM elements
        this.nextDom = this.el.querySelector('#next');
        this.prevDom = this.el.querySelector('#prev');
        this.SliderDom = this.el.querySelector('.carousel .list');
        this.thumbnailBorderDom = this.el.querySelector('.carousel .thumbnail');
        this.thumbnailItemsDom = this.thumbnailBorderDom.querySelectorAll('.item');
        this.sliderItemsDom = this.SliderDom.querySelectorAll('.item');
        this.timeDom = this.el.querySelector('.carousel .time');

        // Auto run the next slide
        this._runNextAuto();

        return this._super(...arguments);
    },

    _onClickNext: function () {
        this._showSlider('next');
    },

    _onClickPrev: function () {
        this._showSlider('prev');
    },

    _onClickThumbnail: function (event) {
        const clickedThumbnail = event.currentTarget;
        const targetIndex = parseInt(clickedThumbnail.getAttribute('data-index'), 10); // Get the index of the clicked thumbnail
        console.log('_onClickThumbnail slide index:', clickedThumbnail.getAttribute('data-index'));

        this._showSliderByIndex(targetIndex);  // Navigate to the corresponding slide
    },

    _showSliderByIndex: function (targetIndex) {
        const SliderItemsDom = Array.from(this.SliderDom.querySelectorAll('.carousel .list .item'));

        // Find the current first slide's index
        const currentIndex = parseInt(SliderItemsDom[0].getAttribute('data-index'));
        console.log('Current first slide index:', currentIndex);
        console.log('targetIndex  slide index:', targetIndex);

        // Calculate the difference between the current index and target index
        const difference = targetIndex - currentIndex;
        console.log('Difference between indices:', difference);

        // Adjust the slider based on the difference
        if (difference > 0) {
            for (let i = 0; i < difference; i++) {
                console.log('SliderItemsDom', i);
                this.nextDom.click();
            }
        } else if (difference < 0) {
            for (let i = 0; i < SliderItemsDom.length + difference; i++) {
                this.nextDom.click();
            }

        }

    },

    _showSlider: function (type) {
        let SliderItemsDom = this.SliderDom.querySelectorAll('.carousel .list .item');
        let thumbnailItemsDom = this.el.querySelectorAll('.carousel .thumbnail .item');

        if (type === 'next') {
            this.SliderDom.appendChild(SliderItemsDom[0]);
            this.thumbnailBorderDom.appendChild(thumbnailItemsDom[0]);
            this.el.classList.add('next');
        } else if (type === 'prev') {
            for (let i = 0; i < SliderItemsDom.length - 1; i++) {
                this.nextDom.click();
            }
            // this.SliderDom.prepend(SliderItemsDom[SliderItemsDom.length - 1]);
            // this.thumbnailBorderDom.prepend(thumbnailItemsDom[thumbnailItemsDom.length - 1]);
            // this.el.classList.add('prev');
        }

        clearTimeout(this.runTimeOut);
        this.runTimeOut = setTimeout(() => {
            this.el.classList.remove('next');
            this.el.classList.remove('prev');
        }, this.timeRunning);

        // Restart auto next timeout
        clearTimeout(this.runNextAuto);
        this._runNextAuto();
    },

    _runNextAuto: function () {
        this.runNextAuto = setTimeout(() => {
            this.nextDom.click();
        }, this.timeAutoNext);
    },
});