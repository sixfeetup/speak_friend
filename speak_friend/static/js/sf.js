(function($) { $(function() {
    // Handle overlay loading
    $('a.overlay').click(function (event) {
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
    $('.modal .close').click(function() {
        $('#overlay').hide();
    });
    
    // Handle overlay form cancel
    // Make sure we don't mess up forms outside of the overlay
    $('#overlay-container #disable-formcancel').click(function() {
        $('#overlay').hide();
        return false;
    });
    
    
    // logout button
    $("#logout-form input").css("display","none");
    $("#logout-link").css("display","block").click(function() {
        $("#logout-btn").click();
    });
    
    // display single checkboxes next to their labels
    var checks = $("input[type='checkbox']:only-child").length;
    for(i = 0; i < checks; i++) {
         $("input[type='checkbox']:only-child").eq(i).parent(".controls").css("display","inline");
         $("input[type='checkbox']:only-child").eq(i).parent(".controls").siblings("label").css("display","inline");
    }
}); })(jQuery);


