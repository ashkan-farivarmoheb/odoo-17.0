/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.VideoControl = publicWidget.Widget.extend({
    selector: '.video_control', // Match this to the class in the HTML
    start: function () {
        console.log("VideoControl widget started"); // Debug start function
        this._super.apply(this, arguments);
        this._initControlVideos();
    },

    _initControlVideos: function () {
        // Get references to the elements
        const video = document.getElementById('video_control'); // Updated to match the video id
        const playPauseBtn = document.getElementById('btnPlayPause');
        const progressBar = document.getElementById('progress-bar');



        // Check if video element exists
        if (!video) {
            console.error("Video element not found");
            return;
        }

        // Play/Pause functionality
        playPauseBtn.addEventListener('click', () => {
            if (video.paused) {
                video.play();
                playPauseBtn.innerHTML = '<i class="fa fa-pause"></i>';  // Change button to pause icon
            } else {
                video.pause();
                playPauseBtn.innerHTML = '<i class="fa fa-play"></i>';   // Change button to play icon
            }
        });

        // Update progress bar as the video plays
        video.addEventListener('timeupdate', () => {
            const progress = (video.currentTime / video.duration) * 100;
            progressBar.value = progress;
        });

        // Allow seeking through the progress bar
        progressBar.addEventListener('input', () => {
            const value = progressBar.value;
            video.currentTime = (value / 100) * video.duration;
        });
    },
});
