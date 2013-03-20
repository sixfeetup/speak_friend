// Handle overlay loading
$(document).ready(function () {
    $('a.overlay').click(function (event) {
        event.preventDefault();
        var url = $(this).attr('href'),
            content_target = $('#overlay-container'),
            overlay = $('#overlay');
        $.ajax({
            url: url,
            success: function (data) {
                content_target.html(data);
                overlay.show();
            }
        });

    });
});

// Handle overlay closing
$(document).ready(function () {
    
    $('#close-overlay').click(function (event) {
        event.preventDefault();
        var target = $('#overlay');
        target.hide();
    });
})

// Handle overlay form cancel
$(document).ready(function () {
    // Make sure we don't mess up forms outside of the overlay
    var selector = '#overlay-container button#deformcancel';
    $(document).on('click', selector, function (event) {
        event.preventDefault();
        var target = $('#overlay');
        target.hide();
    });
});
