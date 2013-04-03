(function() {
  var form = document.querySelector('#command');
  var cmd = form.querySelector('[name="cmd"]');
  var post = form.querySelector('[name="post-processor"]');
  var log = document.querySelector('.responses');
  var master = new WebSocket('ws://localhost:8888/master/');
  var results = [];
  var finishedTimer;
  var postProcessor;

  master.onmessage = function(e) {
    if (finishedTimer) clearTimeout(finishedTimer);
    results.push(e.data);
    finishedTimer = setTimeout(function() {
      if (postProcessor) {
        postProcessor(results);
      } else {
        logResults(results);
      }
    }, 300);
  };

  init();

  function init() {
    bindListeners();
  };

  function logResults(r) {
    var frag = document.createDocumentFragment();
    var node;
    for (var i = 0, l = r.length; i < l; ++i) {
      node = document.createElement('code');
      node.innerHTML = r[i];
      frag.appendChild(node);
    }
    log.appendChild(frag);
  };

  function bindListeners() {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      postCommand(cmd.value);
    });
  };

  function getPostProcessor() {
    var val = post.value;
    if (val == '// Process') { // TODO deal with properly
      return;
    }

    try {
      postProcessor = eval('(function(results){' + val + '})');
      return postProcessor;
    } catch (e) {
      alert('Invalid post-processor specified');
    }
  };

  function postCommand(cmd) {
    postProcessor = getPostProcessor();
    results = [];
    log.innerHTML = '';
    master.send(cmd);
  };
})();
