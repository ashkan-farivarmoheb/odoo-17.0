/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import {loadJS} from '@web/core/assets';

publicWidget.registry.TypeEffect = publicWidget.Widget.extend({
    selector: '.type_effect_title',

    start: function () {
        this._super.apply(this, arguments);
        console.log("TypeEffect widget started");

        // Load Typed.js and initialize after checking edit mode
        loadJS('https://cdn.jsdelivr.net/npm/typed.js@2.0.12').then(() => {
            // console.log("Typed.js library loaded");

            // Initial check for edit mode and observer initialization
            this.checkEditModeAndInit();
            // Code here runs after checkEditModeAndInit has completed

            // Observe changes in the body element
            this.observeEditModeChanges();

        }).catch(error => {
            console.error("Failed to load Typed.js:", error);
        });
    },

    checkEditModeAndInit: async function () {
        const inEditMode = await this.isInEditMode();
        if (!inEditMode) {
            // console.log("Not in edit mode");
            this.initTypeEffect();
        } else {
            // console.log("In edit mode, Typed.js will not be initialized");
            this.destroyTypedEffect();
        }
    },

    isInEditMode: function () {
        return new Promise((resolve) => {
            setTimeout(() => {
                const inEditMode = document.body.classList.contains('editor_enable')
                // console.log("Delayed isInEditMode check:", inEditMode);
                resolve(inEditMode);
            }, 100);  // Adjust delay as needed
        });
    },
    initTypeEffect: function () {
        // console.log("Initializing Typed.js...");
        this.typed = new Typed(".typing_text", {
            strings: [
                "Implementation",
                "Go-Live and Adoption",
                "Training",
                "Customisation",
                "Migration",
                "Integration",
                "Optimisation",
                "Configuration",
                "Scoping and Licensing"
            ],
            typeSpeed: 80,
            backSpeed: 40,
            loop: true,
            cursorChar: '_️',
        });
        // console.log("Typed.js initialized");
    },
    destroyTypedEffect: function () {
        if (this.typed) {
            this.typed.destroy();
            this.typed = null;
            // console.log("Typed.js effect destroyed due to edit mode");
        } else {
            // console.log("No active Typed.js instance to destroy");
        }
    },
    observeEditModeChanges: function () {
        // Create a MutationObserver to observe changes in the DOM
        const observer = new MutationObserver((mutationsList) => {
            for (const mutation of mutationsList) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    // console.log("Class attribute changed on body");
                    this.checkEditModeAndInit();


                }
            }
        });

        // Start observing the body tag for class attribute changes
        observer.observe(document.body, {
            attributes: true, // Observe changes to attributes
            attributeFilter: ['class'], // Only observe the class attribute
        });

        // console.log("MutationObserver initialized to watch for 'editor_has_snippets' class");
    }
});
