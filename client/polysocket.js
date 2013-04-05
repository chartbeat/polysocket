(function() {
  PolySocket = function(config) {
    this.config = config;
    this.connected = false;
    this.createSocket();
  };

  PolySocket.prototype.createSocket = function(address) {
    if (this.socket) {
      throw 'Socket already created';
    }

    this.socket = new WebSocket(this.config.server);
    this.socket.onmessage = this.handleMessage.bind(this);
    this.socket.onopen = this.handleConnected.bind(this);
    this.socket.onclose = this.handleDisconnected.bind(this);
  };

  PolySocket.prototype.handleConnected = function() {
    this.connected = true;
  };

  PolySocket.prototype.handleDisconnected = function() {
    this.connected = false;
  };

  PolySocket.prototype.handleMessage = function(evt) {
    // There can be more than one ], so only take first ocurrence
    // as marking the master ID
    var split = evt.data.split(']');
    var master = split.shift();
    var command = split.join(']');

    try {
      var retVal = eval(command);
      if (retVal) {
        this.socket.send([master, retVal].join(']'));
      }
    } catch (e) {
      this.socket.send([master, e.message].join(']'));
    }
  };

  PolySocket.prototype.transmit = function(message) {
    if (typeof message !== 'string') {
      message = JSON.stringify(message);
    }

    this.socket.send(message);
  };
})();
