$(function() {
  var DOM = {
    form: $('#command'),
    commandInput: $('textarea[name="cmd"]'),
    postProcessor: $('textarea[name="post-processor"]'),
    programList: $('#program-list'),
    saveWindow: $('#save-window'),
    responses: $('.responses')
  };

  var master;
  var results = [];
  var finishedTimer;
  var postProcessor;

  init();

  function init() {
    master = new WebSocket('ws://' + window.location.host + '/master/');
    master.onmessage = handleClientMessage;
    bindListeners();
  };

  function handleClientMessage(e) {
    if (finishedTimer) {
      clearTimeout(finishedTimer);
    }

    results.push(e.data);
    finishedTimer = setTimeout(function() {
      if (postProcessor) {
        postProcessor(results);
      } else {
        logResults(results);
      }
    }, 300);
  }

  function logResults(r) {
    DOM.responses.empty();
    var frag = document.createDocumentFragment();
    var node;
    for (var i = 0, l = r.length; i < l; ++i) {
      node = document.createElement('code');
      node.innerHTML = r[i];
      frag.appendChild(node);
    }

    DOM.responses.append(frag);
    DOM.responses.get(0).scrollTop = DOM.responses.get(0).scrollHeight;
  };

  window.LOG = logResults;

  function loadProgram(p) {
    DOM.commandInput.val(p.command);
    DOM.postProcessor.val(p.postProcessor);
  };

  function bindListeners() {
    $('#run').on('click', function(e) {
      postCommand(DOM.commandInput.val());
    });

    $(window).on('keyup', function(e) {
      if (e.keyCode === 27) {
        $('.slide-window.visible').removeClass('visible');
      }
    });

    $('body').on('click', function(evt) {
      var currentDialog = $('.slide-window.visible');
      var slidingWindow = evt.target.getAttribute('data-slide-window');

      if (currentDialog.get(0) !== evt.target && currentDialog.has(evt.target).length === 0) {
        currentDialog.removeClass('visible');
      }

      if (slidingWindow) {
        $(slidingWindow).addClass('visible');
      }
    });

    DOM.saveWindow.find('form').on('submit', function(e) {
      e.preventDefault();
      var name = DOM.saveWindow.find('[name="name"]').val();
      var command = DOM.commandInput.val();
      var postProcessor = DOM.postProcessor.val() || '';

      if (!name || !command) {
        alert('Missing name or command');
      }

      $.post('/', JSON.stringify({
        'name': name,
        'command': command,
        'postprocessor': postProcessor
      }), function(r) {
        window.location.reload();
      });
    });

    DOM.programList.on('click', function(e) {
      if (e.target.nodeName === 'LI') {
        loadProgram({
          command: e.target.getAttribute('data-command'),
          postProcessor: e.target.getAttribute('data-post-process')
        });

        DOM.programList.removeClass('visible');
      }
    });
  };

  function getPostProcessor() {
    if (!DOM.postProcessor.val()) {
      return;
    }

    try {
      postProcessor = eval('(function(results){' + DOM.postProcessor.val() + '})');
      return postProcessor;
    } catch (e) {
      alert('Invalid post-processor specified');
    }
  };

  function postCommand(cmd) {
    postProcessor = getPostProcessor();
    results = [];
    master.send(cmd);
  };
});
