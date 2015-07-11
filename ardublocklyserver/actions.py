# -*- coding: utf-8 -*-
#
# Collection of actions to the ardublocklyserver for relieved HTTP requests.
#
# Copyright (c) 2015 carlosperate https://github.com/carlosperate/
# Licensed under the Apache License, Version 2.0 (the "License"):
#   http://www.apache.org/licenses/LICENSE-2.0
#
from __future__ import unicode_literals, absolute_import
import subprocess
import time
import json
import os
try:
    # 2.x name
    import Tkinter
    import urlparse
    import tkFileDialog
except ImportError:
    # 3.x name
    import tkinter as Tkinter
    import urllib.parse as urlparse
    import tkinter.filedialog as tkFileDialog

from ardublocklyserver.compilersettings import ServerCompilerSettings
from ardublocklyserver.sketchcreator import SketchCreator
import ardublocklyserver.gui as gui


#
# Sketch loading to Arduino functions
#
def load_arduino_cli(sketch_path=None):
    """
    Launches a subprocess to invoke the Arduino IDE command line to open,
    verify or upload an sketch, the location of which is indicated in the input
    parameter.
    :param sketch_path: Path to the sketch to load into the Arduino IDE.
    :return: A tuple with the following data (success, conclusion, out, error,
            exit_code)
    """
    success = True
    conclusion = error = out = exit_code = ''

    # Input sanitation and output defaults
    if not sketch_path:
        sketch_path = create_sketch_default()
    else:
        if not os.path.isfile(sketch_path):
            conclusion = error = 'Provided sketch path is not a valid file: %s'\
                                 % sketch_path
            success = False
            return success, conclusion, out, error, exit_code

    settings = ServerCompilerSettings()

    # Check if CLI flags have been set
    if not settings.compiler_dir:
        success = False
        conclusion = 'Unable to find Arduino IDE'
        error = 'The compiler directory has not been set.\n' + \
                'Please set it in the Settings.'
    else:
        if not settings.load_ide_option:
            success = False
            conclusion = 'What should we do with the Sketch?'
            error = 'The launch IDE option has not been set.\n' + \
                    'Please select an IDE option in the Settings.'
        elif settings.load_ide_option == 'upload':
            if not settings.get_serial_port_flag():
                success = False
                conclusion = 'Serial Port unavailable'
                error = 'The Serial Port does not exist.\n' + \
                        'Please check if the Arduino is correctly ' + \
                        'connected to the PC and select the Serial Port in ' +\
                        'the Settings.'
            if not settings.get_arduino_board_flag():
                success = False
                conclusion = 'Unknown Arduino Board'
                error = 'The Arduino Board has not been set.\n' + \
                        'Please select the appropriate Arduino Board from ' + \
                        'the settings.'

    if success:
        # Concatenates the CLI command and execute if the flags are valid
        cli_command = [settings.compiler_dir]
        if settings.load_ide_option == 'upload':
            print('\nUploading sketch to Arduino...')
            # This success conclusion message gets overwritten in case of error
            conclusion = 'Successfully Uploaded Sketch'
            cli_command.append('--upload')
            cli_command.append('--port')
            cli_command.append(settings.get_serial_port_flag())
            cli_command.append('--board')
            cli_command.append(settings.get_arduino_board_flag())
        elif settings.load_ide_option == 'verify':
            print('\nVerifying the sketch...')
            # This success conclusion message gets overwritten in case of error
            conclusion = 'Successfully Verified Sketch'
            cli_command.append('--verify')
        elif settings.load_ide_option == 'open':
            print('\nOpening the sketch in the Arduino IDE...')
            conclusion = 'Sketch opened in IDE'
            out = 'The sketch should be loaded in the Arduino IDE.'
        cli_command.append("%s" % sketch_path)
        print('CLI command: %s' % ' '.join(cli_command))

        if settings.load_ide_option == 'open':
            # Open IDE in a subprocess without capturing outputs
            subprocess.Popen(cli_command, shell=False)
            # Wait a few seconds to allow IDE to open before sending back data
            time.sleep(3)
        else:
            # Launch the Arduino CLI in a subprocess and capture output data
            process = subprocess.Popen(
                cli_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False)
            out, error = process.communicate()
            exit_code = str(process.returncode)
            print('Arduino output:\n%s' % out)
            print('Arduino Error output:\n%s' % error)
            print('Arduino Exit code: %s' % exit_code)
            # For some reason Arduino CLI can return 256 on success
            if (process.returncode != 0) and (process.returncode != 256):
                success = False
                if exit_code == str(1):
                    conclusion = 'Build or Upload failed'
                elif exit_code == str(2):
                    conclusion = 'Sketch not found'
                elif exit_code == str(3):
                    conclusion = 'Invalid command line argument'
                elif exit_code == str(4):
                    conclusion =\
                        'Preference passed to "get-pref" flag does not exist'
                else:
                    conclusion = 'Unexpected exit error code: %s' % exit_code

    return success, conclusion, out, error, exit_code


def create_sketch_default():
    settings = ServerCompilerSettings()
    return SketchCreator().create_sketch(
        settings.sketch_dir, sketch_name=settings.sketch_name)


def create_sketch_from_string(sketch_code):
    settings = ServerCompilerSettings()
    return SketchCreator().create_sketch(
        settings.sketch_dir, sketch_name=settings.sketch_name,
        sketch_code=sketch_code)


#
# Compiler Settings
#
def set_compiler_path():
    """
    Opens the file browser to select a file. Saves this file path into
    ServerCompilerSettings and if the file path is different to that stored
    already it triggers the new data to be saved into the settings file.
    """
    new_path = gui.browse_file_dialog()
    if new_path != '':
        ServerCompilerSettings().compiler_dir = new_path
    return get_compiler_path()


def get_compiler_path():
    """
    Creates a JSON string to return to the page with the following format:
    {"response_type" : "settings_compiler",
     "element" : "text_input",
     "display_text" : "Compiler Directory"}
    """
    compiler_directory = ServerCompilerSettings().compiler_dir
    if not compiler_directory:
        compiler_directory = 'Please select a valid Arduino compiler directory'
    json_data = {'setting_type': 'compiler',
                 'element': 'text_input',
                 'display_text': compiler_directory}
    return json.dumps(json_data)


#
# Sketch settings
#
def set_sketch_path():
    """
    Opens the directory browser to select a file. Saves this directory into
    ServerCompilerSettings and if the directory is different to that stored
    already it triggers the new data to be saved into the settings file.
    """
    new_directory = gui.browse_dir_dialog()
    if new_directory != '':
        ServerCompilerSettings().sketch_dir = new_directory
    return get_sketch_path()


def get_sketch_path():
    """
    Creates a JSON string to return to the page with the following format:
    {"response_type" : "settings_sketch",
     "element" : "text_input",
     "display_text" : "Sketch Directory"}
    """
    sketch_directory = ServerCompilerSettings().sketch_dir
    if not sketch_directory:
        sketch_directory = 'Please select a valid Sketch directory.'
    json_data = {'setting_type': 'compiler',
                 'element': 'text_input',
                 'display_text': sketch_directory}
    return json.dumps(json_data)


#
# Arduino Board settings
#
def set_arduino_board(new_value):
    ServerCompilerSettings().arduino_board = new_value
    return get_arduino_boards()


def get_arduino_boards():
    """
    Creates a JSON string to return to the page with the following format:
    {"response_type" : "settings_board",
     "element" : "dropdown",
     "options" : [
         {"value" : "XXX", "text" : "XXX"},
         ...]
     "selected": "selected key"}
    """
    json_data = \
        {'setting_type': 'ide',
         'element': 'dropdown',
         'options': []}
    #TODO: Check for None, however won't happen because static dict in settings
    boards = ServerCompilerSettings().get_arduino_board_types()
    for item in boards:
        json_data['options'].append(
            {'value': item, 'display_text': item})
    json_data.update({'selected': ServerCompilerSettings().arduino_board})
    return json.dumps(json_data)


#
# Serial Port settings
#
def set_serial_port(new_value):
    ServerCompilerSettings().serial_port = new_value
    return get_serial_ports()


def get_serial_ports():
    """
    Creates a JSON string to return to the page with the following format:
    {"response_type" : "settings_serial",
     "element" : "dropdown",
     "options" : [
         {"value" : "XXX", "text" : "XXX"},
         ...]
     "selected": "selected key"}
    """
    json_data = \
        {'setting_type': 'ide',
         'element': 'dropdown',
         'options': []}
    ports = ServerCompilerSettings().get_serial_ports()
    if not ports:
        json_data['options'].append({
            'value': 'no_ports',
            'display_text': 'There are no available Serial Ports'})
        json_data.update({'selected': 'no_ports'})
    else:
        for key in ports:
            json_data['options'].append(
                {'value': key, 'display_text': ports[key]})
        json_data.update({'selected': ServerCompilerSettings().serial_port})
    return json.dumps(json_data)


#
# Load IDE settings
#
def set_load_ide_only(new_value):
    ServerCompilerSettings().load_ide_option = new_value
    return get_load_ide_only()


def get_load_ide_only():
    """
    Creates a JSON string to return to the page with the following format:
    {"response_type" : "settings_ide",
     "element" : "dropdown",
     "options" : [
         {"value" : "XXX", "text" : "XXX"},
         ...]
     "selected": "selected key"}
    """
    json_data = \
        {'setting_type': 'ide',
         'element': 'dropdown',
         'options': []}
    #TODO: Check for None, however won't happen because static dict in settings
    ide_options = ServerCompilerSettings().get_load_ide_options()
    for key in ide_options:
        json_data['options'].append(
            {'value': key, 'display_text': ide_options[key]})
    json_data.update({'selected': ServerCompilerSettings().load_ide_option})
    return json.dumps(json_data)
