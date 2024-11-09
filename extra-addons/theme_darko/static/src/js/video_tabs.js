/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.VideoTab = publicWidget.Widget.extend({
    selector: '.video_tabs_section',
    disabledInEditableMode: false,
    events: {
        'click .title-item': '_onTitleClick',
    },

    start() {
        if (this.editableMode) {
            return this._super(...arguments);
        }

        this.currentIndex = 0;
        this.$videoPlayer = this.$el.find('#feature-video');
        this.$titles = this.$el.find('.title-item');

        if (!this.$videoPlayer.length || !this.$titles.length) {
            return this._super(...arguments);
        }

        this.$videoPlayer.on('ended', () => {
            this._resetProgressBar();
            this._playNextVideo();
        });
        this.$videoPlayer.on('timeupdate', () => this._updateProgressBar());
        this._resetAllProgressBars();
        this._loadVideo(0);

        return this._super(...arguments);
    },

    _onTitleClick(ev) {
        const index = this.$titles.index(ev.currentTarget);
        if (index !== -1) {
            this._resetAllProgressBars();  // Reset all progress bars on tab click
            this.currentIndex = index;
            this._loadVideo(index);
        }
    },

    _loadVideo(index) {
        const $item = this.$titles.eq(index);
        const videoUrl = $item.data('video');
        const cta_href = $item.data('video_cta_href');
        const $ctaButton = this.$el.find('#video-cta');


        // Update video source
        this.$videoPlayer.find('source').attr('src', videoUrl);
        // Log cta_href and $ctaButton

        if ($ctaButton.length && cta_href) {
            $ctaButton.attr('href', cta_href);  // Set the new href from the data attribute
        } else if ($ctaButton.length) {
            // Optional: Handle case when cta_href is missing or invalid
            $ctaButton.hide();  // Hide the CTA button
        }
        // Update active states
        this.$titles.removeClass('active');
        $item.addClass('active');

        // Reset and play video
        const video = this.$videoPlayer[0];
        if (video) {
            video.load();
            video.currentTime = 0;  // Set the video to start from the beginning
            video.muted = true;  // Mute the video to enable autoplay
            if (!this.editableMode) {
                // Wait for the video to be ready and then play it
                video.oncanplaythrough = () => {
                    video.play().catch(console.error);  // Try to play the video
                };
            }
        }
    },

    _playNextVideo() {
        this.currentIndex = (this.currentIndex + 1) % this.$titles.length;
        this._loadVideo(this.currentIndex);
    },

    _updateProgressBar() {
        const video = this.$videoPlayer[0];
        const $currentItem = this.$titles.eq(this.currentIndex);

        if (video && video.duration > 0) {
            const progress = (video.currentTime / video.duration) * 100;
            $currentItem.css('--progress', `${progress}%`);
        }
    },
    _resetProgressBar() {
        const $currentItem = this.$titles.eq(this.currentIndex);
        $currentItem.css('--progress', '0%');
    },
    _resetAllProgressBars() {
        this.$titles.each((index, item) => {
            $(item).css('--progress', '0%');
        });
    },

    destroy() {
        if (this.$videoPlayer) {
            this.$videoPlayer.off('ended timeupdate');
        }
        this._super(...arguments);
    },
});