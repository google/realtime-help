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

"""Views for the realtime help feature."""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from realtime_help import provider

log = logging.getLogger(__name__)


@login_required
def get_init_json(request):
    """Handle GET requests for initial connection. Returns JSON."""
    chat_service_provider = provider.Factory.get_default_provider()

    user_id = str(request.user.id)
    user_pw = user_id
    chat_service_provider.register_user(user_id, user_pw)
    params = {
        'user_jid': '%s@%s' % (
            user_id, chat_service_provider.server_name),
        'user_pw': user_pw,
        'CHAT_DATA_BIND_ENDPOINT': chat_service_provider.chat_url,
    }

    return HttpResponse(json.dumps(params), content_type="text/json")
