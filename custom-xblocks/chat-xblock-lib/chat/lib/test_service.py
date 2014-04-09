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

"""Tests for the chat services logic."""

__author__ = 'Sean Lip (sll@google.com)'

import unittest

import service


class FakeProvider(object):

    def get_active_room_list(self):
        """Returns a list of rooms that are currently in use."""
        return ['room-0', 'room-1']

    def get_room_occupants(self, room_id):
        """Returns a list of user_ids occupying a particular room."""
        if room_id == 'room-full':
            return ['full-occupant-1', 'full-occupant-2']
        elif room_id == 'room-empty':
            return []
        else:
            return []

    def get_helper_jids(self, user_id):
        """Returns a list of helper jids when a request is initiated."""
        return ['helper-1', 'helper-2']

    def send_message(self, recipient_jid, message_body):
        """Sends a message to a user."""
        pass


class ChatServicesTests(unittest.TestCase):

    def setUp(self):
        self.chat_service = service.Chat(FakeProvider())

    def test_get_new_room_id(self):
        self.assertTrue(
            self.chat_service._get_new_room_id().startswith('room-'))

    def test_room_id_generation_fails_if_rooms_are_occupied(self):
        old_max_room_id = service.MAX_ROOM_ID

        service.MAX_ROOM_ID = 1
        with self.assertRaisesRegexp(
                service.RoomGenerationError, 'Could not generate new room'):
            self.chat_service._get_new_room_id()

        service.MAX_ROOM_ID = old_max_room_id

    def test_construct_invitation_stanza(self):
        room_id = 'room-3'
        asker_id = 'asker@example.com',
        asker_href = 'www.edx.org'
        message = 'Hello'

        expected_stanza = (
            '<room_id>%s</room_id><asker_id>%s</asker_id>'
            '<asker_href>%s#%s</asker_href>%s' %
            (room_id, asker_id, asker_href, room_id, message))
        self.assertEqual(
            self.chat_service._construct_invitation_stanza(
                room_id, asker_id, asker_href, message),
            expected_stanza)

    def test_clean_room_if_empty(self):
        room_id_to_owner_display_name = {
            'room-full': 'full_owner',
            'room-empty': 'empty_owner'
        }

        # Nothing happens if the room does not exist..
        self.chat_service._clean_room_if_empty(
            'room-fake', room_id_to_owner_display_name)
        self.assertEqual(room_id_to_owner_display_name, {
            'room-full': 'full_owner',
            'room-empty': 'empty_owner'
        })

        # Non-empty rooms are not cleared.
        self.chat_service._clean_room_if_empty(
            'room-full', room_id_to_owner_display_name)
        self.assertEqual(room_id_to_owner_display_name, {
            'room-full': 'full_owner',
            'room-empty': 'empty_owner'
        })

        # Empty rooms are cleared.
        self.chat_service._clean_room_if_empty(
            'room-empty', room_id_to_owner_display_name)
        self.assertEqual(room_id_to_owner_display_name, {
            'room-full': 'full_owner',
        })

    def test_handle_invitation_acceptance(self):
        user_id_to_room_id = {}
        user_id_to_room_invitations = {
            '123-no-invites': [],
            '456-some-invites': [{
                'time_invited': 1, 'room_id': '456-room',
            }],
        }

        with self.assertRaisesRegexp(
                service.ChatXBlockError,
                'You do not have an invitation to room 456-room'):
            self.chat_service.handle_invitation_acceptance(
                'nonexistent-user', '456-room', user_id_to_room_id,
                user_id_to_room_invitations)

        with self.assertRaisesRegexp(
                service.ChatXBlockError,
                'You do not have an invitation to room 456-room'):
            self.chat_service.handle_invitation_acceptance(
                '123-no-invites', '456-room', user_id_to_room_id,
                user_id_to_room_invitations)

        with self.assertRaisesRegexp(
                service.ChatXBlockError,
                'You do not have an invitation to room other-room'):
            self.chat_service.handle_invitation_acceptance(
                '456-some-invites', 'other-room', user_id_to_room_id,
                user_id_to_room_invitations)

        self.chat_service.handle_invitation_acceptance(
            '456-some-invites', '456-room', user_id_to_room_id,
            user_id_to_room_invitations)
        self.assertEqual(
            user_id_to_room_id, {'456-some-invites': '456-room'})
        self.assertEqual(user_id_to_room_invitations, {
            '123-no-invites': [],
            '456-some-invites': [],
        })

    def test_handle_leave_chat(self):
        user_id = '123'
        user_id_to_room_id = {user_id: 'room-0'}
        room_id_to_owner_display_name = {'room-0': 'name_of_123'}

        self.chat_service.handle_leave_chat(
            user_id, user_id_to_room_id, room_id_to_owner_display_name)

        self.assertEqual(user_id_to_room_id, {})
        self.assertEqual(room_id_to_owner_display_name, {})

    def test_no_errors_if_user_leaves_chat_when_not_in_room(self):
        user_id_to_room_id = {}
        room_id_to_owner_display_name = {}

        self.chat_service.handle_leave_chat(
            'fake-user', user_id_to_room_id, room_id_to_owner_display_name)

    def test_leave_chat_when_others_are_still_in_room(self):
        user_id = '123'
        user_id_to_room_id = {user_id: 'room-full', '456': 'room-full'}
        room_id_to_owner_display_name = {'room-full': 'name_of_123'}

        self.chat_service.handle_leave_chat(
            user_id, user_id_to_room_id, room_id_to_owner_display_name)

        self.assertEqual(user_id_to_room_id, {'456': 'room-full'})
        self.assertEqual(
            room_id_to_owner_display_name, {'room-full': 'name_of_123'})


if __name__ == '__main__':
    unittest.main()
