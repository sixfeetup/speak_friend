(function($) { $(function() {
    // logout button
    $("#logout-form input").css("display","none");
    $("#logout-link").css("display","block").click(function() {
        $("#logout-btn").click();
    });
}); })(jQuery);