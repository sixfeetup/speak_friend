/*
    dependent on zxcvbn.js
    load zxcvbn-async.js in the page, it will load zxcvbn.js
    
    The 'zxcvbn_load_hook' function below will be called when the script load
    is complete.
    
    On key-up it will style a bar positioned with a password input.
    
    The required markup is this:
    
    <input type="password" id="password" name="password" />
    <div class="password-strength">
      <span class="bar">&nbsp;</span>
    </div>
    
    include password_strength.css to get proper styling
    
*/

zxcvbn_load_hook = function() {
  var colorize, handleChange, passwdInput;
  colorize = function (score, target) {
    var colors, color, bar;
    colors = ['e1', 'c2','c4','c6','c8','ca','ac','8c','6c','4c','2c'];
    color = colors[score];
    bar = $(target).next('div.password-strength')
                                     .find('div.bar');
    if (score > 0) {
      bar.css({'width': score + '0%',
               'background-color': "#" + color + "0"});
      if (score > 5) {
          $(".password-strength .weak").css("display","none");
          $(".password-strength .strong").css("display","inline");
      } else {
          $(".password-strength .strong").css("display","none");
          $(".password-strength .weak").css("display","inline");
      }
    } else {
      bar.css({'width': '3px',
               'background-color': "#" + color + "0"});
      $(".password-strength .strong").css("display","none");
      $(".password-strength .weak").css("display","inline");
    }
  };
  handleChange = function (target) {
    var current, last_q, r;
    current = $(target).val();
    if (!current) {
      colorize(0, target);
    } else {
      r = zxcvbn(current);
      colorize(r.score, target);
    }
  };
  passwordInput = $('input[name="password"]');
  handleChange(passwordInput);
  $('input[name="password"]').keyup(function (evt) {
    var target;
    target = $(evt.target);
    handleChange(target);
  });
};