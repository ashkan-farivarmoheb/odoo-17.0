/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.NavbarScroll = publicWidget.Widget.extend({
    selector: 'header',
    start: function () {
        console.log("Navbar Scroll JavaScript is loaded and running!");

        const onScroll = () => {
            console.log("Inside Scroll Event Handler!");
            if (window.scrollY > 0) {
                this.$el.addClass('scrolled');
            } else {
                this.$el.removeClass('scrolled');
            }
        };

        // Attach the scroll event handler to the window
        window.addEventListener('scroll', onScroll);

        // Log a message to confirm the event listener was added
        console.log("Scroll event listener attached to window.");
    }
});
