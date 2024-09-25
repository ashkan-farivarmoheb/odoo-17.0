/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Utility function for debouncing to optimize scroll event handling.
 * Prevents the function from being called too frequently during rapid scrolls.
 * @param {Function} func - The function to debounce.
 * @param {number} wait - The debounce delay in milliseconds.
 * @returns {Function} - The debounced function.
 */


publicWidget.registry.NavbarExtension = publicWidget.Widget.extend({
    selector: '#top',

    start: function () {
        this._super.apply(this, arguments);
        this._initNavbarDropdownListeners();
    },

    /**
     * Initialize listeners for all dropdown toggles within the navbar.
     */
    _initNavbarDropdownListeners: function () {
        const navbar = this.el;
        const dropdownToggles = navbar.querySelectorAll('.o_mega_menu_toggle');
        const dropdownMenus = navbar.querySelectorAll('.o_mega_menu');

        // Convert NodeList to Array for easier handling
        const toggles = Array.from(dropdownToggles);
        const menus = Array.from(dropdownMenus);

        // Variable to keep track of the currently open menu
        let currentlyOpenMenu = null;
        // Flag to indicate if a transition is in progress
        let isTransitioning = false;
        // Transition duration in milliseconds
        const TRANSITION_DURATION = 100; // Adjusted to 100ms for realistic transitions effect when from one open menu switches to open another menu

        /**
         * Opens the specified dropdown menu.
         * @param {HTMLElement} menu - The dropdown menu to open.
         */
        const openMenu = (menu) => {
            isTransitioning = true;
            menu.classList.add('open');
            navbar.classList.add('dropdown-open');
            // Simulate transition duration
            setTimeout(() => {
                isTransitioning = false;
            }, TRANSITION_DURATION);
        };

        /**
         * Closes the specified dropdown menu.
         * @param {HTMLElement} menu - The dropdown menu to close.
         * @param {Function} callback - Function to call after closing.
         */
        const closeMenu = (menu, callback) => {
            isTransitioning = true;
            menu.classList.remove('open');
            navbar.classList.remove('dropdown-open');
            // Simulate transition duration
            setTimeout(() => {
                isTransitioning = false;
                if (callback) callback();
            }, TRANSITION_DURATION);
        };

        toggles.forEach((toggle, index) => {
            const menu = menus[index];
            if (!menu) {
                console.warn(`No corresponding dropdown menu found for toggle at index ${index}.`);
                return;
            }

            // Initial state: Ensure menu is collapsed
            menu.classList.remove('open');

            toggle.addEventListener('click', (event) => {
                event.preventDefault(); // Prevent default link behavior if necessary

                if (isTransitioning) {
                    return; // Ignore clicks during transition
                }

                const isCurrentlyOpen = menu.classList.contains('open');

                if (isCurrentlyOpen) {
                    // If the clicked menu is already open, close it
                    closeMenu(menu, () => {
                        currentlyOpenMenu = null;
                    });
                } else {
                    // If another menu is open, close it first
                    if (currentlyOpenMenu && currentlyOpenMenu !== menu) {
                        closeMenu(currentlyOpenMenu, () => {
                            currentlyOpenMenu = null;
                            // Wait for the transition to complete before opening the new menu
                            setTimeout(() => {
                                openMenu(menu);
                                currentlyOpenMenu = menu;
                            }, TRANSITION_DURATION);
                        });
                    } else {
                        // No other menu is open, simply open the clicked menu
                        openMenu(menu);
                        currentlyOpenMenu = menu;
                    }
                }
            });
        });

        /**
         * Closes any open dropdown menus.
         */
        const closeAllMenus = () => {
            if (currentlyOpenMenu && !isTransitioning) {
                closeMenu(currentlyOpenMenu, () => {
                    currentlyOpenMenu = null;
                });
            }
        };

        /**
         * Handle clicks outside the navbar to close open menus.
         */
        const handleDocumentClick = (event) => {
            if (!navbar.contains(event.target)) {
                closeAllMenus();
            }
        };

        document.addEventListener('click', handleDocumentClick);

        /**
         * Checks if no <a> tags have the 'show' class within #top_menu and closes all menus if true.
         */
        function checkShowClass() {
            // Select the <ul> element by its ID
            const topMenu = document.getElementById('top_menu');

            if (!topMenu) {
                console.error('Element with id "top_menu" not found.');
                return;
            }

            // Query all <a> elements within <li> that have the 'show' class
            const showElements = navbar.querySelectorAll('.o_mega_menu_toggle a.show');

            // If no such elements are found, execute the desired function
            if (showElements.length === 0) {
                closeAllMenus();
            }
        }

        navbar.addEventListener('hidden.bs.dropdown', checkShowClass);
        // Store references for cleanup
        this._dropdownData = {
            handleDocumentClick,
            checkShowClass,
        };


    },
    /**
     * Cleans up event listeners when the widget is destroyed.
     * @override
     */
    destroy: function () {
        const navbar = this.el;

        // Remove document click listener
        if (this._dropdownData && this._dropdownData.handleDocumentClick) {
            document.removeEventListener('click', this._dropdownData.handleDocumentClick);
        }

        // Remove Bootstrap hidden event listener
        if (this._dropdownData && this._dropdownData.checkShowClass) {
            navbar.removeEventListener('hidden.bs.dropdown', this._dropdownData.checkShowClass);
        }

        this._dropdownData = null;

        this._super.apply(this, arguments);
    },
});
