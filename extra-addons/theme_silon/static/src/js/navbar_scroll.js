/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.NavbarScroll = publicWidget.Widget.extend({
    selector: 'main',
    start: function () {
        console.log("Navbar Scroll JavaScript is loaded and running!");

        const onScroll = () => {
            console.log("Inside Scroll Event Handler!");
        };

        // Attach the scroll event handler to the window
        window.addEventListener('scroll', onScroll);

        // Log a message to confirm the event listener was added
        console.log("Scroll event listener attached to window.");
    }
});
