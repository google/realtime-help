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


function Chat(runtime, element) {
  var getChatRoomDataUrl = runtime.handlerUrl(element, 'get_chat_room_data');
  var leaveChatHandlerUrl = runtime.handlerUrl(element, 'leave_chat');

  var getHelpPrompt = $(element).find('.get-help-prompt');
  var chatForm = $(element).find('.chat-form');
  var questionText = $(element).find('.question-text');

  var chatSessionDiv = $(element).find('.chat-session');
  var askerSpan = $(element).find('.asker')[0];

  var closeChatButton = $(element).find('.close-chat');

  var chatAreaDiv = $(element).find('.chat-area');
  var candyIframe = $(element).find('.candy-iframe');
  var candyIframeDoc = candyIframe.contents()[0];

  chatSessionDiv.hide();

  // If a room ID already is determined for this user, use it, regardless of the hash.
  if (chatSessionDiv.data('room-id')) {
    window.location.hash = chatSessionDiv.data('room-id');
    chatSessionDiv.data('room-id', '');
  }

  // The room id is transmitted in the location hash.
  if (window.location.hash) {
    $.ajax({
      url: getChatRoomDataUrl,
      type: 'POST',
      data: JSON.stringify({room_id: window.location.hash.substring(1)}),
      contentType: 'application/json; charset=utf-8',
      success: showChatWindow
    });
  }

  chatForm.submit(function() {
    if (!window.location.hash) {
      $.ajax({
        url: getChatRoomDataUrl,
        type: 'POST',
        data: JSON.stringify({
          question: questionText.val(),
          location: window.location.href
        }),
        contentType: 'application/json; charset=utf-8',
        success: showChatWindow
      });
    }
  });

  closeChatButton.click(function() {
    if (!confirm('This will close your chat session permanently. Are you sure?')) {
      return;
    }

    chatAreaDiv.hide();
    questionText.removeAttr('disabled');
    questionText.val('');
    getHelpPrompt.show();
    chatSessionDiv.hide();
    window.location.hash = '';

    $.ajax({
      url: leaveChatHandlerUrl,
      type: 'POST',
      data: JSON.stringify({}),
      contentType: 'application/json; charset=utf-8',
      success: function(data) {
        window.location.hash = '';
      }
    });
  });

  function showChatWindow(data) {
    if (data.error) {
      alert(data.error_msg);
      return;
    }
    candyIframeDoc.open();
    candyIframeDoc.write(data.chat_iframe_html);
    candyIframeDoc.close();

    askerSpan.textContent = data.room_owner_display_name;
    chatSessionDiv.show();
    getHelpPrompt.hide();
    window.location.hash = data.room_id;
  }
}
