# Copyright 2019 ITS NEW VISION
# Author: Paul Bozan
# License: GNU GPLv2, see LICENSE.txt
import ConfigParser
import importlib
import os
import re
import sys
import signal
import time

import pygame

import datetime
from datetime import datetime
from model import Playlist


# Basic video looper architecure:
#
# - VideoLooper class contains all the main logic for running the looper program.
#
# - Almost all state is configured in a .ini config file which is required for
#   loading and using the VideoLooper class.
#
# - VideoLooper has loose coupling with file reader and video player classes that
#   are used to find movie files and play videos respectively.  The configuration
#   defines which file reader and video player module will be loaded.
#
# - A file reader module needs to define at top level create_file_reader function
#   that takes as a parameter a ConfigParser config object.  The function should
#   return an instance of a file reader class.  See usb_drive.py and directory.py
#   for the two provided file readers and their public interface.
#
# - Similarly a video player modules needs to define a top level create_player
#   function that takes in configuration.  See omxplayer.py and hello_video.py
#   for the two provided video players and their public interface.
#
# - Future file readers and video players can be provided and referenced in the
#   config to extend the video player use to read from different file sources
#   or use different video players.
class VideoLooper(object):

    def __init__(self, config_path):
        """Create an instance of the main video looper application class. Must
        pass path to a valid video looper ini configuration file.
        """
        # Load the configuration.
        self._config = ConfigParser.SafeConfigParser()
        if len(self._config.read(config_path)) == 0:
            raise RuntimeError('Failed to find configuration file at {0}, is the application properly installed?'.format(config_path))
        self._console_output = self._config.getboolean('video_looper', 'console_output')
        # Load configured video player and file reader modules.
        self._player = self._load_player()
        self._reader = self._load_file_reader()
        # Load other configuration values.
        self._osd = self._config.getboolean('video_looper', 'osd')
        self._is_random = self._config.getboolean('video_looper', 'is_random')
        self._keyboard_control = self._config.getboolean('video_looper', 'keyboard_control')
        self._allow_esc_exit = self._config.getboolean('video_looper', 'allow_esc_exit') 
        self._bk_image_path = self._config.get('video_looper', 'bk_image_path')
        self._content_path = self._config.get('directory', 'path')
        # Parse string of 3 comma separated values like "255, 255, 255" into
        # list of ints for colors.
        self._bgcolor = map(int, self._config.get('video_looper', 'bgcolor') \
                                             .translate(None, ',') \
                                             .split())
        self._fgcolor = map(int, self._config.get('video_looper', 'fgcolor') \
                                             .translate(None, ',') \
                                             .split())
        # Load sound volume file name value
        self._sound_vol_file = self._config.get('omxplayer', 'sound_vol_file');
        # default value to 0 millibels (omxplayer)
        self._sound_vol = 0
        # Initialize pygame and display a blank screen.
        pygame.display.init()
        pygame.font.init()
        pygame.mouse.set_visible(False)
        self._size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self._screen = pygame.display.set_mode(self._size, pygame.FULLSCREEN)
        self._blank_screen()
        # Set other static internal state.
        self._extensions = self._player.supported_extensions()
        self._small_font = pygame.font.Font(None, 50)
        self._big_font   = pygame.font.Font(None, 250)
        self._running    = True
        #generate unique device ID
        self._pid=os.popen("cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2 | tail -c 10 | sed -e 's/[^A-Za-z0-9._-]/_/g'").read()[1:-1]


    def _print(self, message):
        """Print message to standard output if console output is enabled."""
        if self._console_output:
            #add datetime in front of printet messages
            now = datetime.now()
            date_time_str = now.strftime("%d/%m/%Y %H:%M:%S")
            print(date_time_str+" : "+message)

    def _load_player(self):
        """Load the configured video player and return an instance of it."""
        module = self._config.get('video_looper', 'video_player')
        return importlib.import_module('.' + module, 'Adafruit_Video_Looper') \
            .create_player(self._config)

    def _load_file_reader(self):
        """Load the configured file reader and return an instance of it."""
        module = self._config.get('video_looper', 'file_reader')
        return importlib.import_module('.' + module, 'Adafruit_Video_Looper') \
            .create_file_reader(self._config)

    def _is_number(iself, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _buildPlaylist(self):
        playlistTh=[]
        playlistRestrictions=[]
        try:
            playlist_path = self._content_path+'/playlist.ini'
            #playlist line example
            #1:=:FILENAME:=:START(%Y%m%d%H%M%S):=:END(%Y%m%d%H%M%S):=:ISTART(%H%M%S):=:IEND(%H%M%S):=:SCREEN_TIME(SECONDS):=:SEND_FEEDBACK(T/F)

            with open(playlist_path) as myfile:
                for line in myfile:
                   self._print("------"+line)
                   split_line = line.split(":=:")
                   order=split_line[0].strip()
                   name=split_line[1].strip()
                   # Display period start time
                   start = None
                   # Display period end time
                   end = None
                   # hourly range start
                   istart = None
                   # hourly range end
                   iend = None
		   # number of seconds to diplay current position
                   screen_time = "-"
		   # log feedback
                   send_feedback = "T"

                   try:
                     start_s=split_line[2].strip()
                     end_s=split_line[3].strip()
                     start = datetime.strptime(start_s, '%Y%m%d%H%M%S')
                     end = datetime.strptime(end_s, '%Y%m%d%H%M%S')
                   except Exception, err:
                     if hasattr(err, 'message'):
                         self._print(err.message)
                     else:
                         self._print(err)
                     pass

                   try:
                     istart_s=split_line[4].strip()
                     iend_s=split_line[5].strip()
                     istart = datetime.strptime(istart_s, '%H%M%S')
                     iend = datetime.strptime(iend_s, '%H%M%S')
                   except Exception, err:
                     if hasattr(err, 'message'):
                        self._print(err.message)
                     else:
                        self._print(err)
                     pass
                   try:
                     int(split_line[6].strip())
                     screen_time=split_line[6].strip()
                   except Exception, err:
                     screen_time=10
                     if hasattr(err, 'message'):
                        self._print(err.message)
                     else:
                        self._print(err)
                     pass
                   try:
                     if split_line[7].strip() == "T":
                      send_feedback = "T"
                     else :
                      send_feedback = "F"
                   except Exception, err:
                     send_feedback = "T"
                     if hasattr(err, 'message'):
                        self._print(err.message)
                     else:
                        self._print(err)
                     pass

                   play_restriction={
                        "start":start,
                        "end":end,
                        "istart":istart,
                        "iend":iend,
                        "screen_time":screen_time,
                        "send_feedback":send_feedback
                   }
                   self._print(order+" - "+name+" - "+screen_time+" - "+str(play_restriction))
                   fullPath=self._content_path+'/'+name
                   if not os.path.exists(fullPath):
                     continue
                   playlistTh.append(fullPath)
                   playlistRestrictions.append(play_restriction)
        except Exception, err:
            self._print("error");
            if hasattr(err, 'message'):
                self._print(err.message)
            else:
                self._print(err)
            pass
        return Playlist(playlistTh,playlistRestrictions,self._is_random)

    def _blank_screen(self):
        """Render a blank screen filled with the background color."""
        self._screen.fill(self._bgcolor)
        pygame.display.update()

    def _blank_screen_no_update(self):
        """Render a blank screen filled with the background color."""
        self._screen.fill(self._bgcolor)

    def _set_background_image(self,playlist):
        """Render background image
           and load bg from disk if playlist index =0 
        """
        try:
           self._screen.blit(self._bk, (0, 0))
           pygame.display.update()
        except Exception, e:
           print('Failed to set background image '+ str(e))

    def _load_bg(self,playlist):
        try:
            isNewIteration = playlist.is_new_iteration()
            if isNewIteration:
               self._has_bgk_image = False
               bk=pygame.image.load(self._bk_image_path)
               self._bk=pygame.transform.scale(bk, self._size)
               self._has_bgk_image = True
               playlist.reset_new_iteration()
        except:
            self._print('Background image not found')
            self._has_bgk_image = False
        pass

    def _render_text(self, message, font=None):
        """Draw the provided message and return as pygame surface of it rendered
        with the configured foreground and background color.
        """
        # Default to small font if not provided.
        if font is None:
            font = self._small_font
        return font.render(message, True, self._fgcolor, self._bgcolor)

    def _animate_countdown(self, playlist, seconds=10):
        """Print text with the number of loaded movies and a quick countdown
        message if the on screen display is enabled.
        """
        # Print message to console with number of movies in playlist.
        message = 'Found {0} movie{1}.'.format(playlist.length(), 
            's' if playlist.length() >= 2 else '')
        self._print(message)
        # Do nothing else if the OSD is turned off.
        if not self._osd:
            return
        # Draw message with number of movies loaded and animate countdown.
        # First render text that doesn't change and get static dimensions.
        label1 = self._render_text(message + ' Starting playback in:')
        l1w, l1h = label1.get_size()
        sw, sh = self._screen.get_size()
        for i in range(seconds, 0, -1):
            # Each iteration of the countdown rendering changing text.
            label2 = self._render_text(str(i), self._big_font)
            l2w, l2h = label2.get_size()
            # Clear screen and draw text with line1 above line2 and all
            # centered horizontally and vertically.
            self._screen.fill(self._bgcolor)
            self._screen.blit(label1, (sw/2-l1w/2, sh/2-l2h/2-l1h))
            self._screen.blit(label2, (sw/2-l2w/2, sh/2-l2h/2))
            pygame.display.update()
            # Pause for a second between each frame.
            time.sleep(1)

    def _idle_message(self):
        """Print idle message from file reader."""
        # Print message to console.
        message = self._reader.idle_message()
        self._print(message)
        # Do nothing else if the OSD is turned off.
        if not self._osd:
            return
        # Display idle message in center of screen.
        label = self._render_text(message)
        lw, lh = label.get_size()
        sw, sh = self._screen.get_size()
        self._screen.fill(self._bgcolor)
        self._screen.blit(label, (sw/2-lw/2, sh/2-lh/2))
        # If keyboard control is enabled, display message about it
        if self._keyboard_control:
            label2 = self._render_text('press ESC to quit')
            l2w, l2h = label2.get_size()
            self._screen.blit(label2, (sw/2-l2w/2, sh/2-l2h/2+lh))
        pygame.display.update()

    def _wait_content_message(self, seconds=10):
        """Print idle message while no content found."""
        # Print message to console.
        message = "Waiting for content..."
        self._print(message)
        for i in range(seconds, 0, -1):
           # Display waiting message in center of screen.
           message = self._pid+" is waiting for content /"
           if(i % 2):
               message = self._pid+" is waiting for content \\"
               label = self._render_text(message)
               lw, lh = label.get_size()
               sw, sh = self._screen.get_size()
               self._screen.fill(self._bgcolor)
               self._screen.blit(label, (sw/2-lw/2, sh/2-lh/2))
               pygame.display.update()
               # A second pause between changing frames.
               time.sleep(1)

    def _prepare_to_run_playlist(self, playlist):
        """Display messages when a new playlist is loaded."""
        # If there are movies to play show a countdown first (if OSD enabled),
        # or if no movies are available show the idle message.
        if playlist.length() > 0:
            self._animate_countdown(playlist)
            self._blank_screen()
        else:
            self._idle_message()

    def _send_play_feedback(self,filename,send_feedback):
        if(send_feedback=='T'):            
            self._print("Play started: "+filename);
            # Place here your code to record play feedback
            # you can use self._pid to identify the player

    def run(self):
        """Main program loop.  Will never return!"""
        # Get playlist of movies to play from file reader.
        playlist = self._buildPlaylist()
        self._prepare_to_run_playlist(playlist)
        self._prevImage = False
        # It stores the beginning of the display period.
        current_position_start_time = time.time()
        # It stores the number of seconds to display the current position
        current_position_screen_time = None
        # It stores the name of current file
        feedback_file_name = ""
        # It can be "T" or "F". It is an attribute of the current position. If "T" - log feedback, if "F" - feedback will be NOT logged.
        send_feedback = "T"
        # if movie is started in loop mode or not
        isMovieLoop = False
        # if current position is an image and is on screen
        isPictureDisplayed = False
        # current playlist index
        cIndex = 0
	# if back KEY is pressed
        isPrevKey = False
        # Main loop to play videos in the playlist and listen for file changes.
        while self._running:
            # Load and play a new movie if nothing is playing.
            if not self._player.is_playing() and not isPictureDisplayed:
                movie = playlist.get_next()
                self._load_bg(playlist)
                if movie is not None:
                    cIndex = playlist.get_current_index()
                    self._print("---------------------------"+repr(cIndex)+"-"+movie+"-------------------------")
                    filename, file_extension = os.path.splitext(movie)
                    file_extension = file_extension.lower()
                    send_feedback = playlist.get_movie_send_feedback(cIndex)
                    #test if current position is jpg or png
                    if (file_extension == ".jpg") or (file_extension == ".png"):
                        realName = os.path.basename(movie)
                        img = pygame.image.load(movie)
                        img = pygame.transform.scale(img, self._size)
                        self._screen.blit(img, (0,0))
                        pygame.display.flip()
                        isPictureDisplayed = True
                        current_position_start_time = time.time()
                        current_position_screen_time = playlist.get_position_screen_time(cIndex)
                        self._prevImage = True
                        # Record play feedback
                        self._send_play_feedback(realName,send_feedback)
                    #current position is a video file
                    else:
                        if self._has_bgk_image and not self._prevImage and not isPrevKey:
                             #sleep one more second in order to have background visible
                             time.sleep(1)
                        self._prevImage = False
                        current_position_start_time = time.time()
                        current_position_screen_time = playlist.get_position_screen_time(cIndex)
                        onlyOneActive = playlist.onlyOneActive()
                        if onlyOneActive and current_position_screen_time is not None:
                           isMovieLoop = True
                           feedback_file_name = os.path.basename(movie)
			else:
                           isMovieLoop = False
                        self._player.play(movie,loop=onlyOneActive, vol=self._sound_vol)
                        if not isPrevKey:
                           time.sleep(1)
                        isPrevKey = False
                        # Call WS to register video play sesion
                        self._send_play_feedback(str(os.path.basename(movie)),send_feedback)
                        nextPosition = playlist.whats_next();
                        # if nextPosition is an image then will be drawn in background to prevent black screen between playlist positions
                        if nextPosition is not None:
                            filenameN, file_extensionN = os.path.splitext(nextPosition)
                            file_extensionN = file_extensionN.lower()
                            if (file_extensionN == ".jpg") or (file_extensionN == ".png"):
                               self._print('Display next image in order to prevent black screen : {0}'.format(nextPosition))
                               img = pygame.image.load(nextPosition)
                               img = pygame.transform.scale(img, self._size)
                               self._screen.blit(img, (0,0))
                               pygame.display.flip()
                            else:
                               if self._has_bgk_image and not self._prevImage:
                                  self._set_background_image(playlist)
                               else:
                                  self._blank_screen()
                        else:
                            if self._has_bgk_image and not self._prevImage:
                               self._set_background_image(playlist)
                            else:
                               self._blank_screen()
                else:
                   self._print('No content.....: {0}')
                   self._blank_screen()
                   self._wait_content_message()

            # Check for changes in the file search path (like USB drives added)
            # and rebuild the playlist. It will never happen because self._reader.is_changed() will return false(hardcoded).
            if self._reader.is_changed():
                self._player.stop(3)  # Up to 3 second delay waiting for old
                                      # player to stop.
                # Rebuild playlist and show countdown again (if OSD enabled).
                playlist = self._buildPlaylist()
                self._prepare_to_run_playlist(playlist)
                self._prevImage = False

            # Event handling for key press, if keyboard control is enabled
            if self._keyboard_control:
            	for event in pygame.event.get():
                   if event.type == pygame.KEYDOWN:
                      self._print("Key="+repr(event.key))
                      # If pressed key is ESC quit program
                      if event.key == pygame.K_ESCAPE and self._allow_esc_exit:
                         self._print("Exit")
                         self.quit()
                      if event.key == pygame.K_RIGHT: 
                         self._print("Go forward")
                         if isPictureDisplayed :
                            isPictureDisplayed = False
                         elif self._player.is_playing():
                            self._player.stop(3)
                      if event.key == pygame.K_LEFT: 
                         self._blank_screen()
                         prev = playlist.set_prev_index()
                         self._print("Go back:"+repr(prev))
                         isPrevKey = True
                         if isPictureDisplayed :
                            isPictureDisplayed = False
                         elif self._player.is_playing():
                            self._player.stop(3)
                      break

            # omxplayer loop call feedback after each play
            if isMovieLoop and current_position_screen_time is not None :
                elapsed_sec = time.time() - current_position_start_time
                if elapsed_sec >= current_position_screen_time:
                   current_position_start_time = time.time()
                   self._send_play_feedback(feedback_file_name,send_feedback)
                   if not playlist.is_on_schedule(cIndex):
                      isMovieLoop = False
                      self._prevImage = False
                      self._player.stop(3)
                      self._prevImage = False
            # test if picture screen time is up. If yes, play next position
            if isPictureDisplayed and current_position_screen_time is not None :
                elapsed_sec = time.time() - current_position_start_time
                if elapsed_sec >= current_position_screen_time:
                   self._print("Picture time's up")
                   isPictureDisplayed = False

	    # Give the CPU some time to do other tasks.
            time.sleep(0.02)

    def quit(self):
        """Shut down the program"""
        self._running = False
        if self._player is not None:
            self._player.stop()
        pygame.quit()

    def signal_quit(self, signal, frame):
        """Shut down the program, meant to by called by signal handler."""
        self.quit()


# Main entry point.
if __name__ == '__main__':
    print('Starting Adafruit Video Looper.')
    # Default config path to /boot.
    config_path = '/boot/video_looper.ini'
    # Override config path if provided as parameter.
    if len(sys.argv) == 2:
        config_path = sys.argv[1]
    # Create video looper.
    videolooper = VideoLooper(config_path)
    # Configure signal handlers to quit on TERM or INT signal.
    signal.signal(signal.SIGTERM, videolooper.signal_quit)
    signal.signal(signal.SIGINT, videolooper.signal_quit)
    # Run the main loop.
    videolooper.run()
