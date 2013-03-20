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
