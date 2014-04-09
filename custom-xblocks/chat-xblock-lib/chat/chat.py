# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Chat XBlock."""

__author__ = 'Sean Lip (sll@google.com)'

import jinja2
import json
import os
import re
import urllib

from lib import service

import pkg_resources
from xblock.core import XBlock
from xblock.fragment import Fragment
from xblock.fields import Dict, Scope

from realtime_help import provider


class ChatBlock(XBlock):
    """XBlock for chat."""

    STUDENT_TEMPLATE_PATH = 'public/html/chat_template.html'
    CHAT_IFRAME_TEMPLATE_PATH = 'public/html/chat_iframe_template.html'
    STUDENT_JS_PATH = 'public/js/chat_player.js'

    user_id_to_room_id = Dict(
        help=('Mapping from user ID to their current room ID for this usage. '
              'Only includes users who have a current room ID.'),
        scope=Scope.user_state_summary, default={})
    room_id_to_owner_display_name = Dict(
        help='Mapping from room ID to its owner\'s display name',
        scope=Scope.user_state_summary, default={})
    # Each room_invitation is a dict with two keys:
    # - 'time_invited': the time of the invitation in seconds since the Epoch
    # - 'room_id': the id of the room the user was invited to.
    user_id_to_room_invitations = Dict(
        help='Mapping from user ID to a list of room invitations',
        scope=Scope.user_state_summary, default={})

    def _get_error_dict(self, error_code, error_msg):
        """Returns a dict used to send error messages to the frontend."""
        return {
            'error': error_code,
            'error_msg': error_msg,
        }

    @property
    def _chat_provider(self):
        return provider.Factory.get_default_provider()

    @property
    def _chat_service(self):
        return service.Chat(self._chat_provider)

    @property
    def _jinja_env(self):
        """A Jinja environment for rendering templates."""
        def _js_string_filter(value):
            """Converts a value to a JSON string for use in JavaScript code."""
            string = json.dumps(value)

            replacements = [('\\', '\\\\'), ('"', '\\"'), ("'", "\\'"),
                            ('\n', '\\n'), ('\r', '\\r'), ('\b', '\\b'),
                            ('<', '\\u003c'), ('>', '\\u003e'),
                            ('&', '\\u0026')]

            for replacement in replacements:
                string = string.replace(replacement[0], replacement[1])
            return jinja2.utils.Markup(string)

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
            extensions=['jinja2.ext.autoescape'],
            autoescape=True)
        env.filters.update({
            'js_string': _js_string_filter,
        })
        return env

    @classmethod
    def open_local_resource(cls, uri):
        """Overwrite the superclass's open_local_resource() method.

        This is done to allow periods in the folder and file names, to allow a
        final .map extension, and to allow a hashtag at the end.
        """
        assert re.match(
            r'^public/([a-zA-Z0-9\.\-_]+/)*[a-zA-Z0-9\.\-_]+\.'
            '(jpg|jpeg|png|gif|js|css|json|map)(#\.+)?$', uri
        ), uri
        assert '..' not in uri
        return pkg_resources.resource_stream(cls.__module__, uri)

    def _get_resource_string(self, path):
        """Returns a resource string for use in add_css(), add_javascript()."""
        return unicode(pkg_resources.resource_string(
            __name__, path).decode('utf-8', 'ignore'))

    def _get_current_user_id(self):
        """Returns the current user id."""
        return str(self.scope_ids.user_id)

    def _get_current_username(self):
        """Get the username of the current user."""
        # TODO(sll): This is a stub; it should be fixed to return the actual
        # username.
        return 'Student%s' % self._get_current_user_id()

    def _get_chat_html_dict(self, room_id, user_id, subject=''):
        """Get a dict containing data about the chat room to populate the HTML.

        If a non-empty 'subject' argument is passed, a new subject line is
        added to the chat window.
        """
        params = {
            'CHAT_DATA_BIND_ENDPOINT': self._chat_provider.chat_url,
            'CANDY_LIB_URL': self.runtime.local_resource_url(
                self, 'public/lib/candy'),
            'ROOM_SERVER_NAME': self._chat_provider.room_server_name,
            'SERVER_NAME': self._chat_provider.server_name,
            'display_name': self._get_current_username(),
            'room_id': room_id,
            'subject': subject,
            'user_id': user_id,
        }
        chat_iframe_html = self._jinja_env.get_template(
            self.CHAT_IFRAME_TEMPLATE_PATH).render(params)

        return {
            'chat_iframe_html': chat_iframe_html,
            'room_id': room_id,
            'room_owner_display_name': (
                self.room_id_to_owner_display_name[room_id]),
        }

    def student_view(self, context):
        """Provide the default student view."""
        # WARNING: This assumes that the XBlock container does not refresh
        # or redirect pages so that the location hash disappears. It also
        # assumes that there are no other hashes.

        user_id = self._get_current_user_id()
        room_id = self.user_id_to_room_id.get(user_id, '')

        frag = Fragment(self._jinja_env.get_template(
            self.STUDENT_TEMPLATE_PATH).render({'room_id': room_id}))
        frag.add_css(self._get_resource_string(
            'public/lib/candy/res/default.css'))
        frag.add_css(self._get_resource_string('public/css/chat.css'))
        frag.add_javascript(self._get_resource_string(self.STUDENT_JS_PATH))
        js_dep_paths = [
            'public/lib/candy/libs/libs.min.js',
            'public/lib/candy/candy.bundle.js',
        ]
        for js_dep_path in js_dep_paths:
            frag.add_javascript(self._get_resource_string(js_dep_path))

        frag.initialize_js('Chat')
        return frag

    @XBlock.json_handler
    def get_chat_room_data(self, data, suffix=''):
        """Returns information needed for the client to launch a chat room."""
        user_id = self._get_current_user_id()

        # If the user is currently assigned to a chat room, serve data for
        # that room.
        current_room_id = self.user_id_to_room_id.get(user_id)
        if current_room_id is not None:
            return self._get_chat_html_dict(current_room_id, user_id)

        # Otherwise, if the user has just accepted an invitation, process this
        # event and serve data for that room.
        invited_room_id = data.get('room_id')
        if invited_room_id is not None:
            try:
                self._chat_service.handle_invitation_acceptance(
                    user_id, invited_room_id, self.user_id_to_room_id,
                    self.user_id_to_room_invitations)
                return self._get_chat_html_dict(invited_room_id, user_id)
            except service.ChatXBlockError as e:
                return self._get_error_dict(400, str(e))

        # Otherwise, if a new subject has been entered, create a new chat
        # room, send out invitations, and add the user to it.
        try:
            asker_location = data['location']
            asker_question = data['question']
            subject = urllib.quote(asker_question)
        except KeyError:
            return self._get_error_dict(
                400, 'Unspecified location or question.')

        asker_display_name = self._get_current_username()
        try:
            new_room_id = self._chat_service.handle_start_new_chat(
                user_id, asker_display_name, asker_location, asker_question,
                self.user_id_to_room_id, self.room_id_to_owner_display_name,
                self.user_id_to_room_invitations)
        except service.ChatXBlockError as e:
            return self._get_error_dict(400, str(e))

        return self._get_chat_html_dict(
            new_room_id, user_id, subject=subject)

    @XBlock.json_handler
    def leave_chat(self, data, suffix=''):
        """Leaves a chat room."""
        user_id = self._get_current_user_id()
        self._chat_service.handle_leave_chat(
            user_id, self.user_id_to_room_id,
            self.room_id_to_owner_display_name)
        return {}
