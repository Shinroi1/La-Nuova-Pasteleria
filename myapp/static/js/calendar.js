document.addEventListener("DOMContentLoaded", function () {
    console.log("Disabled Dates from Django:", disabledDates);  // Must now be an array

    flatpickr("#datepicker", {
        enableTime: true,
        dateFormat: "Y-m-d\\TH:i",
        disableMobile: true,
        disable: disabledDates,
        minDate: "today"
    });
});
