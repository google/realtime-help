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

import urllib2


# FIXME: Replace this with the IP address for the ejabberd chat server.
EJABBERD_CHAT_SERVER_IP_ADDRESS = '1.2.3.4'


class Ejabberd(object):

    @property
    def chat_url(self):
        """The BOSH URL for connections to the ejabberd chat server."""
        return str(
            'https://%s:80/http-bind/' % EJABBERD_CHAT_SERVER_IP_ADDRESS)

    @property
    def admin_url(self):
        """The mod_rest endpoint for the ejabberd chat server admin console.

        This must correspond to the {hosts} setting in ejabberd.cfg: see
        http://www.ejabberd.im/node/9831 .
        """
        return str('https://%s:5285/rest/' % EJABBERD_CHAT_SERVER_IP_ADDRESS)

    @property
    def server_name(self):
        """The name of the ejabberd chat server used for registering users."""
        return 'localhost'

    @property
    def room_server_name(self):
        """The name of the multi-user chat room server."""
        return 'conference.localhost'

    def _make_post_request(self, payload):
        """Makes a POST request to the chat server admin endpoint."""
        req = urllib2.Request(self.admin_url, payload)
        response = urllib2.urlopen(req)
        return response.read()

    def get_helper_jids(self, asker_jid):
        """Returns a list of helper jids when a request is initiated.

        Args:
          asker_id: str. The jid of the asker.

        Returns:
          list of str: The jids of the students to ping for help.
        """
        response = self._make_post_request('connected_users')
        results = response.split('\n')
        # ejabberd returns a single 0 if no users are connected.
        if results == ['0']:
            return []

        return [
            candidate_jid for candidate_jid in results
            if not candidate_jid.startswith(asker_jid)]

    def get_active_room_list(self):
        """Returns a list of rooms that are currently in use."""
        response = self._make_post_request(
            'muc_online_rooms %s' % self.room_server_name[:len('conference.')])
        room_addresses = response.split('\n')
        return [room_address.split('@')[0] for room_address in room_addresses]

    def get_room_occupants(self, room_id):
        """Returns a list of user_ids occupying a particular room."""
        response = self._make_post_request(
            'get_room_occupants %s %s' % (room_id, self.room_server_name))
        occupants = response.split('\n')
        return [occupant[:occupant.find('@')] for occupant in occupants]

    def send_message(self, recipient_jid, message_body):
        """Sends a message to a user.

        Args:
          recipient_jid: str. The JID of the recipient.
          message_body: str. The XML stanza to be transmitted within the outer
            <message/> tags.
        """
        payload = (
            '<message xmlns="jabber:client" from="%s/rest" to="%s" '
            'type="chat">%s</message>' %
            (self.server_name, recipient_jid, message_body))
        self._make_post_request(payload)

    def register_user(self, user_id, password):
        """Registers a user if the user isn't already registered."""
        self._make_post_request('register %s %s %s' % (
            user_id, self.server_name, password))


class Factory(object):
    """Factory methods that construct a realtime help provider."""

    @classmethod
    def get_default_provider(self):
        return Ejabberd()
