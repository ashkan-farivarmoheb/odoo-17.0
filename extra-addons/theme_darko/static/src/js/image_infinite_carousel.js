/** @odoo-module */
// import publicWidget from '@web/legacy/js/public/public_widget';
//
// const InfiniteCarousel = publicWidget.Widget.extend({
//     selector: '.image_infinit_carousel_section',  // Updated selector to match template
//
//     /**
//      * @override
//      */
//     start() {
//         console.log("Carousel widget is starting...");
//         this._initCarousel();
//         return this._super(...arguments);
//     },
//
//     /**
//      * Initialize the infinite carousel
//      * @private
//      */
//     _initCarousel() {
//         console.log("Initializing carousel...");
//         const allImageCarousels = this.el.querySelectorAll("[data-rc-carousel]");
//         console.log("Found carousels:", allImageCarousels);
//
//         allImageCarousels.forEach((carousel) => {
//             this._setupCarouselItems(carousel);
//         });
//     },
//
//     /**
//      * Setup carousel items by cloning and setting properties
//      * @private
//      * @param {HTMLElement} carousel - The carousel element to setup
//      */
//     _setupCarouselItems(carousel) {
//         const allItems = carousel.querySelectorAll("[data-rc-carousel-item]:not(.cloned)");
//         console.log('all-items:', allItems);  // Logs all items to inspect
//
//
//         // Calculate total width of all images
//         let totalWidth = 0;
//         let itemCount = 0;
//         allItems.forEach((item) => {
//             const img = item.querySelector("img");
//             if (img) {
//                 totalWidth += img.offsetWidth; // Add image width to total width
//                 itemCount++;
//             }
//         });
//
//         // Calculate average width
//         const averageWidth = totalWidth / itemCount;
//         console.log('Total width: ', totalWidth);
//         console.log('Item count: ', itemCount);
//         console.log('Average width: ', averageWidth);
//
//         // Set --tile-size to average width
//         carousel.style.setProperty("--tile-size", `${averageWidth}px`);
//         allItems.forEach((item, index) => {
//             console.log(`Cloning item ${index + 1} of ${allItems.length}`);
//             const itemToClone = item.cloneNode(true);
//             itemToClone.setAttribute("aria-hidden", "true");
//             itemToClone.classList.add("cloned");
//
//             const carouselBox = carousel.querySelector("[data-rc-carousel-box]");
//             if (carouselBox) {
//                 carouselBox.insertAdjacentElement("beforeend", itemToClone);
//                 console.log(`Inserted cloned item ${index + 1} into carousel.`);
//             } else {
//                 console.log("Carousel box not found.");
//             }
//         });
//
//         // Logging the number of tiles being set
//         console.log('Setting --tiles CSS property to:', allItems.length * 2);
//         carousel.style.setProperty("--tiles", allItems.length * 2);
//     },
//
//     /**
//      * Clean up when the widget is destroyed
//      * @override
//      */
//     destroy() {
//         console.log("Destroying carousel widget...");
//         const clonedElements = this.el.querySelectorAll(".cloned");
//         clonedElements.forEach(element => {
//             console.log("Removing cloned element:", element);
//             element.remove();
//         });
//         this._super(...arguments);
//     },
// });
//
// publicWidget.registry.InfiniteCarousel = InfiniteCarousel;

import publicWidget from '@web/legacy/js/public/public_widget';
import EditModeDetector from './EditModeDetector';  // Adjust the path if needed


const InfiniteCarousel = publicWidget.Widget.extend({
    selector: '.image_infinit_carousel_section',

    start() {
         // Initialize the edit mode detector and pass the callback to handle mode change
        this.editModeDetector = new EditModeDetector((inEditMode) => {
            if (inEditMode) {
                console.log("Editor mode detected. Carousel initialization skipped.");
                this.destroy();  // Stop the carousel if in edit mode
            } else {
                console.log("Not in editor mode. Initializing carousel.");
                this._initCarousel();  // Initialize carousel if not in edit mode
            }
        });

        return this._super(...arguments);
    },

    _initCarousel() {
        // console.log("Initializing carousel...");
        const allImageCarousels = this.el.querySelectorAll("[data-rc-carousel]");
        // console.log("Found carousels:", allImageCarousels);

        allImageCarousels.forEach((carousel) => {
            this._setupCarouselItems(carousel);
        });
    },

    _setupCarouselItems(carousel) {
        // Only select items without the cloned class
        const allItems = carousel.querySelectorAll("[data-rc-carousel-item]:not(.cloned)");
        // console.log('All items:', allItems);

        // Calculate total width of all images
        let totalWidth = 0;
        let itemCount = 0;
        allItems.forEach((item) => {
            const img = item.querySelector("img");
            if (img) {
                totalWidth += img.offsetWidth;
                itemCount++;
            }
        });

        // Calculate average width and set as tile size
        const averageWidth = totalWidth / itemCount;
        // console.log('Average width:', averageWidth);
        carousel.style.setProperty("--tile-size", `${averageWidth}px`);

        // Clone items
        allItems.forEach((item, index) => {
            // console.log(`Cloning item ${index + 1} of ${allItems.length}`);
            const itemToClone = item.cloneNode(true);
            itemToClone.setAttribute("aria-hidden", "true");
            itemToClone.classList.add("cloned");

            const carouselBox = carousel.querySelector("[data-rc-carousel-box]");
            if (carouselBox) {
                carouselBox.insertAdjacentElement("beforeend", itemToClone);
                // console.log(`Inserted cloned item ${index + 1} into carousel.`);
            } else {
                // console.log("Carousel box not found.");
            }
        });

        // console.log('Setting --tiles CSS property to:', allItems.length * 2);
        carousel.style.setProperty("--tiles", allItems.length * 2);
    },


    destroy() {
        // console.log("Destroying carousel widget...");
        const clonedElements = this.el.querySelectorAll(".cloned");
        clonedElements.forEach(element => {
            // console.log("Removing cloned element:", element);
            element.remove();
        });
        this._super(...arguments);
                console.log("Carousel destroyed.");

    },
});

publicWidget.registry.InfiniteCarousel = InfiniteCarousel;
export default InfiniteCarousel;
