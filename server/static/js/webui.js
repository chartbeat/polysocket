(function() {
  var form = document.querySelector('#command');
  var cmd = form.querySelector('.code-entry');

  init();

  function init() {
    bindListeners();
  };

  function bindListeners() {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      postCommand(cmd.value);
    });
  };

  function postCommand(cmd) {
    var xhr = new XMLHttpRequest;
    var map = {
      cmd: cmd
    };

    xhr.open('POST', '/cmd/', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify(map));
  };
})();
