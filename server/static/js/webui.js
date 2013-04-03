(function() {
  var form = document.querySelector('#command');
  var cmd = form.querySelector('[name="cmd"]');
  var post = form.querySelector('[name="post-processor"]');
  var programList = document.querySelector('#program-list');
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

  window.LOG = logResults;

  function loadProgram(p) {
    cmd.value = p.command;
    post.value = p.postProcessor;
  };

  function bindListeners() {
    document.querySelector('#run').addEventListener('click', function() {
      postCommand(cmd.value);
    });

    document.querySelector('#load').addEventListener('click', function() {
      toggleProgramList();
    });

    programList.addEventListener('click', function(e) {
      if (e.target.nodeName === 'LI') {
        loadProgram({
          command: e.target.getAttribute('data-command'),
          postProcessor: e.target.getAttribute('data-post-process')
        });
      }
      toggleProgramList();
    });
  };

  function toggleProgramList() {
    if (programList.className == 'visible') {
      programList.className = '';
    } else {
      programList.className = 'visible';
    }
  };

  function getPostProcessor() {
    if (!post.value) {
      return;
    }

    try {
      postProcessor = eval('(function(results){' + post.value + '})');
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
