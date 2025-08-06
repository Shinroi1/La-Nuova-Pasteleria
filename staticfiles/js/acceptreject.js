function acceptReservation(entryId) {
    sendActionToServer(entryId, 'accept');
}

function rejectReservation(entryId) {
    sendActionToServer(entryId, 'reject');
}

function sendActionToServer(entryId, action) {
    fetch(adminVerificationUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),  // To ensure CSRF protection
        },
        body: JSON.stringify({ entry_id: entryId, action: action })
    })
    .then(response => response.json())
    .then (data => {
        console.log("Server Response:", data);
    if (data.success) {
        alert("Success:" + data.message)
        location.reload(); 
    } else {
        alert("Error: " + data.message);
    }
    })
    .catch(error => {
        console.error("Error:", error);
        alert("An error occurred. Please check the console and try again.");
    });
}

function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

