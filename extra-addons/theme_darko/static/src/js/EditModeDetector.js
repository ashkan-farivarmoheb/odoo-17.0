/** @odoo-module **/

export default class EditModeDetector {
    constructor(callback) {
        this.callback = callback;
        this.isInEditMode = this._checkEditMode();

        // Immediately run callback if already in edit mode
        this.callback(this.isInEditMode);

        // Observe class changes for edit mode toggle
        this._observeEditModeChanges();
    }

    // Method to check if we're in edit mode based on body class
    _checkEditMode() {
        return document.body.classList.contains('editor_enable');
    }

    // Method to handle changes and invoke callback if mode changes
    _observeEditModeChanges() {
        const observer = new MutationObserver(() => {
            const currentMode = this._checkEditMode();
            if (currentMode !== this.isInEditMode) {
                this.isInEditMode = currentMode;
                this.callback(this.isInEditMode);
            }
        });

        // Observe the body element for class changes
        observer.observe(document.body, {
            attributes: true,
            attributeFilter: ['class'],
        });
    }
}
