// Copyright 2014 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


var NOTIFICATIONS = {
  // The text to prepend to the invitation message.
  INVITATION_PREFIX: 'Help Chat Notification',
  // The main notification object.
  Notification: {
    connection: null,
    handleMessage: function(message) {
      var messageContents = $(message).contents();
      var roomId = messageContents[0].textContent;
      var askerId = messageContents[1].textContent;
      var askerUrl = messageContents[2].textContent;
      var messageBody = decodeURIComponent(messageContents[3].data);

      showInvitationMsgInButterBar(messageBody, roomId, askerUrl);
      return true;
    }
  },
  NOTIFICATIONS_URL_ENDPOINT: '/realtime_help/notifications'
};


function ButterBar(popup, message, close) {
  this.popup = popup;
  this.message = message;
  this.close = close;
}
ButterBar.getButterBar = function() {
  return new ButterBar(document.getElementById('chat-notifications'),
    document.getElementById('chat-notifications-message'),
    document.getElementById('chat-notifications-close'));
};
function hideMsg() {
  var butterBar = ButterBar.getButterBar();
  if ($(butterBar.popup).hasClass('shown')) {
    $(butterBar.popup).removeClass('shown');
  }
}
ButterBar.keepInView = function() {
  var popup = ButterBar.getButterBar().popup;
  var container = popup.parentElement;

  container.style.top = null;
  $(container).removeClass('fixed');

  var offset = $(popup).offset().top;
  if (offset - $(document).scrollTop() <= 10) {
    $(container).addClass('fixed');
    container.style.top = (10 - popup.offsetTop) + 'px';
    container.style.right = $('body').find('.inner-wrapper').css('marginRight');
  }
};


function showInvitationMsgInButterBar(message, roomId, askerUrl) {
  var butterBar = ButterBar.getButterBar();

  $(butterBar.message).empty();

  var messageElt = document.createElement('span');
  messageElt.appendChild(document.createTextNode(message));
  butterBar.message.appendChild(messageElt);

  var linkElt = document.createElement('a');
  linkElt.setAttribute('href', askerUrl);
  linkElt.setAttribute('target', '_blank');
  linkElt.className = 'chat-notifications-help-link';
  linkElt.appendChild(document.createTextNode('Join chat'));
  linkElt.onclick = hideMsg;
  butterBar.message.appendChild(linkElt);

  if (!$(butterBar.popup).hasClass('shown')) {
    $(butterBar.popup).addClass('shown');
  }
  if (butterBar.close != null) {
    butterBar.close.onclick = hideMsg;
  }
  $(window).on('scroll', ButterBar.keepInView);
}


function createNotificationsDiv() {
  var notificationDiv = document.createElement('div');
  notificationDiv.className = 'chat-notifications-container';

  var topElement = document.createElement('div');
  topElement.id = 'chat-notifications';
  topElement.className = 'chat-notifications';
  topElement.setAttribute('aria-live', 'polite');

  var closeElement = document.createElement('a');
  closeElement.className = 'chat-notifications-close';
  closeElement.id = 'chat-notifications-close';
  closeElement.textContent = 'X';

  var headerElement = document.createTextNode(NOTIFICATIONS.INVITATION_PREFIX);
  headerElement.className = 'chat-notifications-header';
  headerElement.id = 'chat-notifications-header';

  var messageElement = document.createElement('p');
  messageElement.className = 'chat-notifications-message';
  messageElement.id = 'chat-notifications-message';

  topElement.appendChild(closeElement);
  topElement.appendChild(headerElement);
  topElement.appendChild(document.createElement('br'));
  topElement.appendChild(messageElement);

  notificationDiv.appendChild(topElement);

  var courseTabsDiv = $('body').find('.course-tabs')[0];
  courseTabsDiv.appendChild(notificationDiv);
}


$(function() {
  $.get(NOTIFICATIONS.NOTIFICATIONS_URL_ENDPOINT, function(data) {
    // Do not do anything if chat is not enabled for this course.
    if (data.error) {
      return;
    }

    createNotificationsDiv();

    var Notification = NOTIFICATIONS.Notification;
    Notification.connection = new Strophe.Connection(
        data.CHAT_DATA_BIND_ENDPOINT);
    Notification.connection.connect(
        data.user_jid, data.user_pw, function(status) {
      if (status === Strophe.Status.CONNECTED) {
        console.log('Connected.');
        Notification.connection.addHandler(
            Notification.handleMessage, null, 'message', 'chat');
      } else if (status === Strophe.Status.DISCONNECTED) {
        console.log('Disconnected.');
      }
    });
  }, 'json');
});
