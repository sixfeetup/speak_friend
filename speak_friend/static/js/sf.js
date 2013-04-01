(function($) { $(function() {
    // Handle overlay loading
    $('a.overlay').on('click', function (event) {
        var url = $(this).attr('href'),
            content_target = $('#overlay-container'),
            overlay = $('#overlay'),
            row = $(this).parents('tr').first();

        // Save the row so our other handlers can get it.
        window.row = row;

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
        window.row = null;
    });

    function changeUserClass(row) {
        if (row.attr('class').trim() !== 'disabled') {
            row.attr('class', 'disabled');
        } else {
            row.attr('class', '');
        }
    }

    function changeFormButtonText(row) {
        var button = row.find('a.overlay'),
            text = button.text(),
            new_text = '';

        if (text.indexOf("Disable") >= 0) {
            new_text = text.replace("Disable", "Enable");
        }

        if (text.indexOf("Enable") >= 0) {
            new_text = text.replace("Enable", "Disable");
        }

        button.text(new_text);

    }

    // Submitting the disable user form.
    $('#overlay').on('click', '#overlay-container #disable-formsubmit', function(event) {
        event.preventDefault();
        var form_data = $('#disable-form').serialize(),
            content_target = $('#overlay-container'),
            url = $('#disable-form').attr('action');

        $.ajax({
            type: "POST",
            url: url,
            data: form_data,
            success: function(data) {
                content_target.html(data);
                if (window.row !== null) {
                    changeUserClass(window.row);
                    changeFormButtonText(window.row);
                    window.row = null;
                }
            }
        });
    });

    // Handle overlay form cancel
    // Make sure we don't mess up forms outside of the overlay
    $('#overlay').on('click', '#overlay-container #disable-formcancel', function(event) {
        $('#overlay').hide();
        window.row = null;
    });
    
    // logout button
    $("#logout-form input").css("display","none");
    $("#logout-link").css("display","block").on('click', function() {
        $("#logout-btn").click();
    });

    $('.tableHeader').on('click', function(event) {
        var column_name = $(this).attr('data-column'),
            form = $('#usersearch'),
            column_field = $('#usersearch input[name=column]');
        column_field.val(column_name);
        form.submit()
    });

    // display single checkboxes next to their labels
    var checks = $("input[type='checkbox']:only-child").length;
    for(i = 0; i < checks; i++) {
         $("input[type='checkbox']:only-child").eq(i).parent(".controls").css("display","inline");
         $("input[type='checkbox']:only-child").eq(i).parent(".controls").siblings("label").css("display","inline");
    }
}); })(jQuery);


