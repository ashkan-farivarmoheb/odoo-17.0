/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.VideoOnScroll = publicWidget.Widget.extend({
    selector: '.video_onScroll_section',
    start: function () {
        this._super.apply(this, arguments);
        this._initScrollVideos();
    },

    _initScrollVideos: function () {
        // Function to register video scroll interaction
        const registerVideo = (boundSelector, videoSelector) => {
            const bound = document.querySelector(boundSelector);
            const video = document.querySelector(videoSelector);

            const scrollVideo = () => {
                if (video.duration) {
                    const distanceFromTop = window.scrollY + bound.getBoundingClientRect().top;
                    const scrollableHeight = bound.scrollHeight - window.innerHeight;
                    const scrollYWithinBound = window.scrollY - distanceFromTop;

                    // Only update the video if within scrollable bounds
                    if (scrollYWithinBound >= 0 && scrollYWithinBound <= scrollableHeight) {
                        const percentScrolled = scrollYWithinBound / scrollableHeight;
                        video.currentTime = video.duration * percentScrolled;
                    }
                }
                requestAnimationFrame(scrollVideo);
            };
            requestAnimationFrame(scrollVideo);
        };

        // Register the video with scrolling logic
        registerVideo(".scroll-section", ".scroll-section video");
    },
});
