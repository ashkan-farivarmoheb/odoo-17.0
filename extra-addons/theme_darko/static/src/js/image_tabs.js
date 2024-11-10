/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.ImageTab = publicWidget.Widget.extend({
    selector: '.image_tabs_section',
    disabledInEditableMode: false,
    events: {
        'click .title-item': '_onTitleClick',
    },

    start() {
        if (this.editableMode) {
            return this._super(...arguments);
        }

        this.currentIndex = 0;
        this.$imageElement = this.$el.find('#feature-image');
        this.$titles = this.$el.find('.title-item');
        this.$donutProgress = this.$el.find('.donut-progress');  // Select donut element

        if (!this.$imageElement.length || !this.$titles.length || !this.$donutProgress.length) {
            return this._super(...arguments);
        }

        this._resetAllProgressBars();
        this._loadImage(0);

        // Start the automatic transition for images with progress updates
        this._startAutoPlay();

        return this._super(...arguments);
    },

    _startAutoPlay() {
        const defaultDuration = 5000; // Default duration in case no custom duration is set
        const intervalDuration = parseInt(getComputedStyle(this.$imageElement[0]).getPropertyValue('--interval-duration')) || defaultDuration;

        const progressUpdateInterval = 50; // Frequency of progress update in milliseconds

        // Interval to switch to the next image after the specified duration
        this.autoPlayInterval = setInterval(() => {
            this._playNextImage();
        }, intervalDuration);

        // Interval to update the progress bar
        this.progressInterval = setInterval(() => {
            this._updateProgressBar(intervalDuration, progressUpdateInterval);
        }, progressUpdateInterval);
    },

    _loadImage(index) {
        // Select the title item at the specified index
        const $item = this.$titles.eq(index);

        // Retrieve the image URL and CTA link from the data attributes
        const imageUrl = $item.data('image');
        const ctaHref = $item.data('image_cta_href');
        const $ctaButton = this.$el.find('#image-cta');

        // Update the image source to the new URL
        this.$imageElement.attr('src', imageUrl);

        // If the CTA button exists and the link is available, update it
        if ($ctaButton.length && ctaHref) {
            $ctaButton.attr('href', ctaHref);
            $ctaButton.show();  // Show the button if there's a link
        } else if ($ctaButton.length) {
            $ctaButton.hide();  // Hide the button if there's no link
        }

        // Update the active state for the current title item
        this.$titles.removeClass('active');  // Clear active state for all items
        $item.addClass('active');  // Set active state for the current item

        // Reset the progress bar for the newly loaded image
        this._resetProgressBar();
    }
    ,
    _updateProgressBar(duration, interval) {
        const $currentItem = this.$titles.eq(this.currentIndex);
        let currentProgress = parseFloat($currentItem.css('--progress')) || 0;
        const progressIncrement = (interval / duration) * 100;

        currentProgress += progressIncrement;
        if (currentProgress > 100) {
            currentProgress = 0;  // Reset when reaching 100%
        }

        $currentItem.css('--progress', `${currentProgress}%`);

        // Update the donut's stroke-dashoffset to create a countdown effect
        const donutOffset = 100 - currentProgress;
        this.$donutProgress.css('stroke-dashoffset', donutOffset);
    },

    _resetProgressBar() {
        const $currentItem = this.$titles.eq(this.currentIndex);
        $currentItem.css('--progress', '0%');
        this.$donutProgress.css('stroke-dashoffset', '100');  // Reset donut progress
    },

    _resetAllProgressBars() {
        this.$titles.each((index, item) => {
            $(item).css('--progress', '0%');
        });
        this.$donutProgress.css('stroke-dashoffset', '100');  // Reset donut for all
    },

    _resetAutoPlay() {
        clearInterval(this.autoPlayInterval);
        clearInterval(this.progressInterval);
    },

    _playNextImage() {
        this.currentIndex = (this.currentIndex + 1) % this.$titles.length;
        this._resetAllProgressBars();
        this._loadImage(this.currentIndex); // Load the next image and reset progress
    },

    _onTitleClick(ev) {
        const index = this.$titles.index(ev.currentTarget);
        if (index !== -1) {
            this._resetAutoPlay();  // Pause auto-play on click
            this._resetAllProgressBars();
            this.currentIndex = index;
            this._loadImage(index);
            this._startAutoPlay();  // Restart auto-play after manual interaction
        }
    },

    destroy() {
        this._resetAutoPlay();  // Clear all intervals on destroy
        this._super(...arguments);
    },
});
