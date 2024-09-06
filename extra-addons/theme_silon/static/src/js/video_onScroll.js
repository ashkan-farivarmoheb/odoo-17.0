/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.VideoOnScroll = publicWidget.Widget.extend({
    selector: '.video_onScroll_section',
    start: function () {
        this._super.apply(this, arguments);
        this._initScrollVideos();
    },
    // faster play= shorter min-height e.g 100vh
    // slower play= longer min-height e.g 500vh
    //   .scroll-section {
    //     background: transparent;
    //     min-height: 1000vh; /* Increase to make the video play more slowly */
    //   }
    _initScrollVideos: function () {
        // Function to register video scroll interaction
        const registerVideo = (boundSelector, videoSelector) => {
            const bound = document.querySelector(boundSelector);
            const video = document.querySelector(videoSelector);

            // Log to ensure correct elements are targeted
            console.log('Bound Element:', bound);
            console.log('Video Element:', video);

            if (!bound || !video) {
                console.error("Could not find bound or video element.");
                return;
            }

            // Track the previous time for smoother updates
            let previousTime = 0;

            const scrollVideo = () => {
                if (video.duration) {
                    // Get the position and dimensions related to scrolling
                    const distanceFromTop = window.scrollY + bound.getBoundingClientRect().top;
                    const scrollableHeight = bound.scrollHeight - window.innerHeight;
                    const scrollYWithinBound = window.scrollY - distanceFromTop;

                    // Commented off these logs
                    /*
                    console.log('Video Duration:', video.duration);
                    console.log('Distance from Top:', distanceFromTop);
                    console.log('Scrollable Height:', scrollableHeight);
                    console.log('Scroll Y Within Bound:', scrollYWithinBound);
                    */

                    // Ensure we're within the scrollable area
                    if (scrollYWithinBound >= 0 && scrollYWithinBound <= scrollableHeight) {
                        // Calculate the percentage scrolled
                        let percentScrolled = scrollYWithinBound / scrollableHeight;

                        // Clamp the percentage to the 0-1 range to avoid overflows
                        percentScrolled = Math.min(1, Math.max(0, percentScrolled));

                        const targetTime = video.duration * percentScrolled;

                        // console.log('Percent Scrolled (adjusted):', percentScrolled);
                        // console.log('Target Video Time:', targetTime);

                        // Update the video current time
                        video.currentTime = targetTime;

                        // Log current video time for debugging
                        // console.log('Updated Video Time:', video.currentTime);

                        previousTime = video.currentTime;
                    }
                }

                // Continue the animation loop
                requestAnimationFrame(scrollVideo);
            };

            // Start the scroll event-driven video update
            requestAnimationFrame(scrollVideo);
        };

        // Register the video with scrolling logic
        registerVideo(".scroll-section", ".scroll-section video");
    },
});
