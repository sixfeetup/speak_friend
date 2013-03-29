(function($) { $(function() {
    // Handle overlay loading
    $('a.overlay').on('click', function (event) {
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
        return false;
    });
    
    // Handle overlay closing
    $('#overlay').on('click', '.modal .close', function(event) {
        $('#overlay').hide();
    });
    
    // Handle overlay form cancel
    // Make sure we don't mess up forms outside of the overlay
    $('#overlay').on('click', '#overlay-container #disable-formcancel', function(event) {
        $('#overlay').hide();
    });
    
    
    // logout button
    $("#logout-form input").css("display","none");
    $("#logout-link").css("display","block").on('click', function() {
        $("#logout-btn").click();
    });
    
    // display single checkboxes next to their labels
    var checks = $("input[type='checkbox']:only-child").length;
    for(i = 0; i < checks; i++) {
         $("input[type='checkbox']:only-child").eq(i).parent(".controls").css("display","inline");
         $("input[type='checkbox']:only-child").eq(i).parent(".controls").siblings("label").css("display","inline");
    }
}); })(jQuery);


