/*
Error message extraction from API responses

FastAPI error responses typically aren't a simple string but a structured JSON object. 
Sometimes details can be a string, but often it's an array of error objects, each containing a "msg" field with the error message.
If we dump that error into the UI without processing, it can look messy and confusing to users.
This function checks if the error detail is a string or an array of error objects and extracts the relevant messages accordingly. 
If the structure is unexpected, it returns a generic error message.
*/
export function getErrorMessage(error) {
    if (typeof error.detail === "string") {
        return error.detail;
    }
    else if (Array.isArray(error.detail)) {
        return error.detail.map((err) => err.msg).join(". ");
    }
    return "An error occurred. Please try again.";
}

// Show a Bootstrap modal by ID
// Helper function to show a Bootstrap modal by its ID. It uses the Bootstrap Modal API to get or create an instance of the modal and then shows it.
export function showModal(modalId) {
    const modal = bootstrap.Modal.getOrCreateInstance(
        document.getElementById(modalId),
    );
    modal.show();
    return modal;
}

// Hide a Bootstrap modal by ID
// Helper function to hide a Bootstrap modal by its ID. It retrieves the existing instance of the modal and calls the hide method. If the modal instance doesn't exist, it does nothing.
export function hideModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) modal.hide();
}

// We export these functions so they can be imported and used in other parts of our application,
// such as in event handlers or API response processing logic.
// This modular approach keeps our code organized and reusable.