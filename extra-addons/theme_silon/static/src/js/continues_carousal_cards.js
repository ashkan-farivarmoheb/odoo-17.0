/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.continuesCarouselSlider = publicWidget.Widget.extend({
    selector: '.continues-carousel',

    start: function () {
        var self = this;
        this.$carousel = this.$el.is('.carousel') ? this.$el : this.$('.carousel');
        this.$carouselInner = this.$carousel.find('.continues-carousel-inner');
        this.$carouselItems = this.$carouselInner.find('.continues-carousel-item');
        this.$indicators = this.$carousel.find('.continues-carousel-indicators li');
        this.totalItems = this.$carouselItems.length;
        this.currentIndex = 0;
        this.cardWidth = this.$carouselItems.first().outerWidth(true);
        this.visibleItems = Math.floor(this.$carousel.width() / this.cardWidth);  // Number of items visible at a time
        this.$nextArrow = this.$carousel.find('.carousel-control-next'); // Reference to the next arrow
        this.$prevArrow = this.$carousel.find('.carousel-control-prev'); // Reference to the prev arrow
        this.totalItems = this.$carouselItems.length;

        console.log('Carousel initialized with total items:', this.totalItems);
        console.log('Card width:', this.cardWidth);

        this.$carousel.on('slide.bs.carousel', function (e) {
            console.log('Slide event triggered:', e.direction);

            if (e.direction === 'left') {
                self.currentIndex += 1;
                if (self.currentIndex >= self.totalItems - self.visibleItems + 1) {
                    self.currentIndex = 0;
                }
            } else {
                self.currentIndex -= 1;
                if (self.currentIndex < 0) {
                    self.currentIndex = self.totalItems - self.visibleItems;
                }
            }

            var transformValue = `translateX(-${self.currentIndex * self.cardWidth}px)`;
            console.log('Transforming carousel to:', transformValue);
            self.$carouselInner.css('transform', transformValue);
            self.$carouselInner.css('transition', "transform 0.5s ease");

            // Update the indicators
            console.log('Updating indicators, current index:', self.currentIndex);
            self.$indicators.removeClass('active').eq(self.currentIndex).addClass('active');

            // Hide/show the next arrow based on current index
            if (self.currentIndex >= self.totalItems - self.visibleItems) {
                console.log('Hiding next arrow');
                self.$nextArrow.addClass('d-none');
            } else {
                console.log('Showing next arrow');
                self.$nextArrow.removeClass('d-none');
            }

            // Hide/show the prev arrow based on current index
            if (self.currentIndex === 0) {
                console.log('Hiding prev arrow');
                self.$prevArrow.addClass('d-none');
            } else {
                console.log('Showing prev arrow');
                self.$prevArrow.removeClass('d-none');
            }

            e.preventDefault();  // Prevent default slide behavior
        });

        // Handle indicator click
        this.$indicators.on('click', function () {
            console.log('Indicator clicked:', $(this).index());

            self.currentIndex = $(this).index();
            var transformValue = `translateX(-${self.currentIndex * self.cardWidth}px)`;
            console.log('Transforming carousel to:', transformValue);
            self.$carouselInner.css('transform', transformValue);
            self.$carouselInner.css('transition', "transform 0.5s ease");

            // Update the indicators
            console.log('Updating indicators, current index:', self.currentIndex);
            self.$indicators.removeClass('active').eq(self.currentIndex).addClass('active');

            // Hide/show the next arrow based on current index
            if (self.currentIndex >= self.totalItems - self.visibleItems) {
                console.log('Hiding next arrow');
                self.$nextArrow.addClass('d-none');
            } else {
                console.log('Showing next arrow');
                self.$nextArrow.removeClass('d-none');
            }

            // Hide/show the prev arrow based on current index
            if (self.currentIndex === 0) {
                console.log('Hiding prev arrow');
                self.$prevArrow.addClass('d-none');
            } else {
                console.log('Showing prev arrow');
                self.$prevArrow.removeClass('d-none');
            }
        });
    }
});

export default {
    continuesCarouselSlider: publicWidget.registry.continuesCarouselSlider,
};
