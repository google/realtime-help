Realtime-help chat XBlock and notifications service
===================================================

An XBlock_ and associated notification service that allows students in an edX_
course to ask each other for help with course material in real time.

.. _XBlock: https://github.com/edx/XBlock
.. _edX: https://www.edx.org


Description
-----------

In the offline world, students who are working together on a homework
assignment can easily ask each other for help if they get stuck. However,
in an online course, these students are generally not located in the same
place, and they may be taking the course at different times. This makes it
harder to replicate the real-time help experience, despite the fact that
online courses tend to have many more participants, and therefore more people
for a particular student to seek help from.

This code repository contains a realtime-help XBlock (together with a
notification service) that enables students to ask other students for help
in real-time. Authors of edX courses can add this XBlock to a course page.
When a student is stuck on a problem, he/she can type a question into this
XBlock, which will then be broadcast to other students taking the course.
The recipients of the broadcast can then join the original student’s chat
room, and help him/her to address the problem.

The code release is made up of an XBlock and a small Django app for
broadcasting chat notifications. Both of these components make use of
ejabberd_, a popular open-source instant messaging server, to keep track
of rooms and student presence. The XBlock provides an interface that allows
students to join and participate in chats on a specific course page, and the
notification app runs on all course pages so that it can detect whether
students are present in order to broadcast questions to them.

.. _ejabberd: http://www.ejabberd.im/


Requirements
------------

You will need access to two servers: one for the ejabberd chat service and one
for the edX platform. Documentation_ for ejabberd is available at the ejabberd
website. Please note that this code has only been tested on Ubuntu Linux
12.04 servers.

Instructions for provisioning these servers are provided below. Please note
that the code in this repository has been developed against commit 78fe797e_
of edx-platform, and may need to be modified in order to be compatible with
later versions of the edX platform.

For both servers, you will need a Bash environment to run the installation
script, which uses standard development tools, including ``git``.

The code includes the strophejs_ library (v1.1.1), as well as a modified
version of the Candy_ chat library (v1.6.0).

.. _Documentation: http://www.process-one.net/docs/ejabberd/guide_en.html
.. _78fe797e: https://github.com/edx/edx-platform/commit/78fe797e145a8fbc3baf01f9ff1dc70c411bc2de
.. _strophejs: http://strophe.im/strophejs/
.. _Candy: http://candy-chat.github.io/candy/


Installation instructions for the ejabberd server
-------------------------------------------------

Note: Log files for ejabberd can be found at ``/var/log/ejabberd/ejabberd.log``
and ``/var/log/ejabberd/erlang.log``. If any issues occur during installation,
it should be possible to figure out what went wrong by examining these.

  1.  Ensure that ports 80 and 5285 on this server are able to accept
      incoming TCP traffic. (Port 80 is used for connections by students, and
      port 5285 is used for connections to the ejabberd admin console.) Only
      the edX server should be allowed to communicate with port 5285.

  2.  Copy the ``ejabberd-setup`` folder in this repository to the server.

  3.  In a terminal, navigate to the ejabberd-setup/ directory and execute the
      command:

      ::

        bash setup_ejabberd.sh

  4.  Create a .PEM certificate file, ``server.pem``, which has a
      ``BEGIN CERTIFICATE`` section followed by a ``BEGIN PRIVATE KEY``
      section. Make a note of its location in the file system; you will need
      this later.

      Note: If you are working in development mode, these instructions_ explain
      how to generate a self-signed .PEM certificate file:

      ::

        openssl req -x509 -days 365 -nodes -newkey rsa:1024 -keyout key.pem -out cert.pem

      Concatenate ``cert.pem`` and ``key.pem`` to get the ``server.pem`` file:

      ::

        cat cert.pem key.pem > server.pem

      Warning: If you use a self-signed certificate, it will not be accepted by
      Chrome. You will need to visit ``{{CHAT_SERVER_IP_ADDRESS}}:5285/rest``
      and ``{{CHAT_SERVER_IP_ADDRESS}}:80/http-bind/`` in your browser, and
      click 'Proceed Anyway'.

  5.  Open /etc/ejabberd/ejabberd.cfg and search for the four places which say
      ``REALTIME_HELP_FIXME``. Follow the instructions in the comments at each
      of these places. You will need to add:

      (a) the IP address of the ejabberd server
      (b) (in 2 places) the location of the ``server.pem`` file
      (c) the IP address of the edX server

  6.  Launch the ejabberd service by running the following command from a
      terminal:

      ::

        sudo ejabberdctl start

      Note that this command does not produce any output in the terminal. You
      can check to see if the service is running by inspecting the logs at
      ``/var/log/ejabberd/ejabberd.log``.

  7.  (Optional) You can test the connection to the ejabberd server by running
      the following command in a terminal from a machine that is allowed to
      access it:

      ::

        wget https://{{EJABBERD_SERVER_IP}}:5285/rest/ --server-response --post-data 'muc_online_rooms global' --no-check-certificate

      where {{EJABBERD_SERVER_IP}} is the IP address of the ejabberd server.

      If it hangs, check that the URL is correct and that the right ports are
      open, and also check the ejabberd log files for any unexpected errors.
      If it returns a 406 error, ensure that the IP address you are making
      the request from is an allowed IP in the ``ejabberd.cfg`` file.

.. _instructions: http://how2ssl.com/articles/openssl_commands_and_tips/


Installation instructions for the edX server
--------------------------------------------

Please note that, as of April 1, 2014, the following instructions have been
tested against commit 78fe797e_ of edx-platform. However, due to the evolving
nature of XBlocks and the edx-platform, you might instead wish to consult the
latest installation instructions for XBlocks. Documentation for this can be
found in the XBlock_ and edx-platform_ repos.

  1.  Install edX as described in the official edX documentation_. (In
      addition, you may wish to either sync to commit 78fe797e_ of
      ``edx-platform``, or modify the code in this repository so that it
      works with the version of ``edx-platform`` you installed. Instructions
      for syncing to a particular version can be found on this wiki_ page.)

  2.  Navigate to the root of ``edx-platform``. This should be located in
      ``/edx/app/edxapp/edx-platform``.

  3.  In ``cms/djangoapps/contentstore/views/component.py``, add 'chat' to the
      ``ADVANCED_COMPONENT_TYPES`` list.

  4.  In ``lms/envs/common.py``, add the following two dependencies to the
      ``main_vendor_js`` list:

      ::

        'js/vendor/chat-xblock-assets/js/notifications.js',
        'js/vendor/chat-xblock-assets/lib/strophejs/strophe.min.js',

      and add the following dependency to the end of
      ``PIPELINE_CSS['style-vendor']['source-filenames']``:

      ::

        'js/vendor/chat-xblock-assets/css/notifications.css'

  5.  In the ``lms/urls.py`` file, add the line

      ::

        url(r'^realtime_help/', include('realtime_help.urls')),

      to the `urlpatterns` tuple.

  6.  Fix a bug in edx-platform which does not permit it to handle resources
      that have unicode characters in them, by changing line 62 in

      ::
        cms/djangoapps/contentstore/views/item.py

      from ``md5.update(data)`` to ``md5.update(data.encode('utf-8'))``.

      (Note that this error has since been fixed in edx-platform: see this
      commit_ for more details.)

  7.  Copy the ``custom-xblocks`` folder of this repository to a location on
      the server, such as ``/home/ubuntu/custom-xblocks``. (You may need to
      change the permissions on this folder so that it is accessible by the
      ``edxapp`` user.) After doing this:

      (a) add a symlink from common/djangoapps/realtime_help to
      ``custom-xblocks/realtime_help``:

      ::

        ln -s /home/ubuntu/custom-xblocks/realtime_help common/djangoapps/realtime_help

      (b) add a symlink from common/static/js/vendor/chat-xblock-assets to
      ``custom-xblocks/chat-xblock-lib/chat/public``.

      ::

        ln -s /home/ubuntu/custom-xblocks/chat-xblock-lib/chat/public common/static/js/vendor/chat-xblock-assets

  8.  At the top of the file
      ``/home/ubuntu/custom-xblocks/realtime_help/provider.py``,
      specify ``EJABBERD_CHAT_SERVER_IP_ADDRESS``, the IP address for the ejabberd
      chat server.

  9.  Navigate to custom-xblocks/chat-xblock-lib, and run the command

      ::

        bash setup_chat_xblock.sh

      to download third-party libraries needed for the XBlock.

  10. In the same custom-xblocks/chat-xblock-lib directory, run the command

      ::

        /edx/bin/pip.edxapp install -e .

      to install the XBlock (note the final '.').

  11. Manually compile the assets, following edX's guidelines_.

  12. Restart the edX LMS/CMS servers, following edX's guidelines_.

  Logs for the edX servers can be found in /edx/var/log/cms/edx.log and
  /edx/var/log/lms/edx.log .

.. _documentation: https://github.com/edx/configuration/wiki/Single-AWS-server-installation-using-Amazon-Machine-Image
.. _wiki: https://github.com/edx/configuration/wiki/edX-Managing-the-Production-Stack
.. _78fe797e: https://github.com/edx/edx-platform/commit/78fe797e145a8fbc3baf01f9ff1dc70c411bc2de
.. _commit: https://github.com/edx/edx-platform/pull/3192
.. _guidelines: https://github.com/edx/configuration/wiki/edX-Managing-the-Production-Stack
.. _XBlock: https://github.com/edx/XBlock
.. _edx-platform: https://github.com/edx/edx-platform/blob/master/docs/en_us/developers/source/xblocks.rst


Adding chat functionality to the edX demo course
------------------------------------------------

  1.  In a browser window, navigate to edX Studio, sign in as the default user
      (username 'staff@example.com', password 'edx') and click on the sample
      edX demonstration course.

  2.  In the navigation bar at the top, click on the 'Settings' dropdown menu,
      then click 'Advanced Settings'. Add a new value, "chat", to the
      ``advanced_modules`` policy key. Save the changes.

  3.  Return to the demo course by clicking its name in the navbar. In the
      ``Introduction`` section, add a new subsection called ``Chat``. Add a new
      unit to this section.

  4.  Click the 'advanced' button at the bottom of the screen, and
      select 'Chat' from the options presented. You should now have a chat
      XBlock in the page.


Limitations
-----------
 
Please note that, at present, this code has some limitations
due to the absence of corresponding functionality in the XBlocks
API as of April 1, 2014.

  1.  The chat window does not display the actual usernames of students.
  2.  It may be desirable to restrict the list of invitees for a help session
      to students who have already completed the corresponding lesson page. At
      present, the matching algorithm simply picks five students at random.
  3.  The functionality may not scale to large courses, since the room
      assignment data is stored in XBlock fields which are not queryable
      databases.
  4.  If this XBlock is incorporated into a course, all students will be able
      to send and respond to help requests. There is no functionality for
      allowing individual students to turn helpchat notifications off.
  5.  Chat messages are not scoped to a particular course.

In addition, please note that:

  1.  This code has not undergone an in-depth security review.
  2.  The ejabberd server is not automatically provisioned.
  3.  At most one help chat XBlock should be embedded in each course page.

We hope that this code provides a useful base that others can
build on and modify for use in their edX courses.
