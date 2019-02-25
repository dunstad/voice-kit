#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a recognizer using the Google Assistant Library with button support.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

The Google Assistant Library can be installed with:
    env/bin/pip install google-assistant-library==0.0.2

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import subprocess
import sys
import threading

import aiy.assistant.auth_helpers
import aiy.assistant.device_helpers
import aiy.audio
import aiy.voicehat
from google.assistant.library import Assistant
from google.assistant.library.event import EventType

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)


class MyAssistant(object):
    """An assistant that runs in the background.

    The Google Assistant Library event loop blocks the running thread entirely.
    To support the button trigger, we need to run the event loop in a separate
    thread. Otherwise, the on_button_pressed() method will never get a chance to
    be invoked.
    """
    def __init__(self):
        self._task = threading.Thread(target=self._run_task)
        self._can_start_conversation = False
        self._assistant = None

    def start(self):
        """Starts the assistant.

        Starts the assistant event loop and begin processing events.
        """
        self._task.start()

    def _run_task(self):
        credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
        model_id, device_id = aiy.assistant.device_helpers.get_ids(credentials)
        with Assistant(credentials, model_id) as assistant:
            self._assistant = assistant
            for event in assistant.start():
                self._process_event(event)

    def say(self, text):
        say_volume = 10
        aiy.audio.say(text, volume=say_volume)

    def toggle_tv_power(self):
        self.say('Switching TV power.')
        subprocess.call('node /home/pi/voice-recognizer-raspi/src/tv-control/toggle.js', shell=True)

    def play_youtube(self, query):
        self.say('Playing {0}.'.format(query))
        subprocess.call('node /home/pi/voice-recognizer-raspi/src/tv-control/youtube.js {0}'.format(query.replace("'", "")), shell=True)

    def set_volume(self, volume):
        self.say('Setting volume to {0}.'.format(volume))
        subprocess.call('node /home/pi/voice-recognizer-raspi/src/tv-control/volume.js {0}'.format(volume), shell=True)

    def power_off_pi(self):
        self.say('Good bye!')
        subprocess.call('sudo shutdown now', shell=True)


    def reboot_pi(self):
        self.say('See you in a bit!')
        subprocess.call('sudo reboot', shell=True)


    def say_ip(self):
        ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
        self.say('My IP address is %s' % ip_address.decode('utf-8'))


    def _process_event(self, event):
        status_ui = aiy.voicehat.get_status_ui()
        if event.type == EventType.ON_START_FINISHED:
            status_ui.status('ready')
            self._can_start_conversation = True
            # Start the voicehat button trigger.
            aiy.voicehat.get_button().on_press(self._on_button_pressed)
            if sys.stdout.isatty():
                print('Say "OK, Google" then speak, or press Ctrl+C to quit...')

        elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            self._can_start_conversation = False
            status_ui.status('listening')

        elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
            print('You said:', event.args['text'])
            text = event.args['text'].lower()
            if text == 'power off':
                self._assistant.stop_conversation()
                self.power_off_pi()
            elif text == 'reboot':
                self._assistant.stop_conversation()
                self.reboot_pi()
            elif text == 'ip address':
                self._assistant.stop_conversation()
                self.say_ip()
            elif all(word in text for word in ['turn', 'tv']):
                self._assistant.stop_conversation()
                self.toggle_tv_power()
            elif (text.index('play') if 'play' in text else -1) == 0:
                self._assistant.stop_conversation()
                self.play_youtube(text[text.index(' ') + 1:])
            elif all(word in text for word in ['set', 'volume']):
                self._assistant.stop_conversation()
                self.set_volume(text.split(' ')[-1])



        elif event.type == EventType.ON_END_OF_UTTERANCE:
            status_ui.status('thinking')

        elif event.type == EventType.ON_CONVERSATION_TURN_FINISHED:
            status_ui.status('ready')
            self._can_start_conversation = True

        elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
            sys.exit(1)

    def _on_button_pressed(self):
        # Check if we can start a conversation. 'self._can_start_conversation'
        # is False when either:
        # 1. The assistant library is not yet ready; OR
        # 2. The assistant library is already in a conversation.
        if self._can_start_conversation:
            self._assistant.start_conversation()


def main():
    MyAssistant().start()


if __name__ == '__main__':
    main()


