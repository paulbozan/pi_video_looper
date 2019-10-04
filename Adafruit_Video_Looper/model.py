# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola
# License: GNU GPLv2, see LICENSE.txt
import random
import datetime
from datetime import datetime

class Playlist(object):
    """Representation of a playlist of movies."""

    def __init__(self, movies, playRestrictions, is_random):
        """Create a playlist from the provided list of movies."""
        self._movies = movies
        self._play_restrictions = playRestrictions
        self._index = None
        self._is_random = is_random
        self._new_iteration = True
        self._period_ok = False
        self._interval_ok = False

    def is_on_schedule(self,play_index):
        """Check that the current position (play_index) is within the time range and can be displayed. The function returns True or False. """
        on_schedule = True
        play_restriction=self._play_restrictions[play_index]
        #print(play_restriction)
        if not (play_restriction["start"] is None or play_restriction["end"] is None):
          now = datetime.now()
          if(now>=play_restriction["start"] and now<play_restriction["end"]):
            self._period_ok = True
          else:
            self._period_ok = False
            on_schedule = False
        else:
          self._period_ok = True

        if not (play_restriction["istart"] is None or play_restriction["iend"] is None):
          now = datetime.now().time()
          if(now>=play_restriction["istart"].time() and now<play_restriction["iend"].time()):
            self._interval_ok = True
          else:
            self._interval_ok = False
            on_schedule = False
        else:
          self._interval_ok = True
        
        return on_schedule

    def get_file_meta(self,play_index):
        """Returns the meta information(time range, screen_time, etc) for a playlist index(play_index). """
        play_restriction=self._play_restrictions[play_index]
        return play_restriction

    def get_position_screen_time(self,play_index):
        """Returns the meta information screen_time for a playlist index(play_index). """
        play_restriction=self._play_restrictions[play_index]
        if not (play_restriction["screen_time"] is None or play_restriction["screen_time"]== "-" ):
           return int(play_restriction["screen_time"])
        else:	
           return None

    def get_movie_send_feedback(self,play_index):
        """Returns the meta information send_feedback for a playlist index(play_index). """
        play_restriction=self._play_restrictions[play_index]
        if not (play_restriction["send_feedback"] is None ):
           return play_restriction["send_feedback"]
        else:
           return "F"

    def get_next(self):
        """Get the next movie in the playlist. Will loop to start of playlist
        after reaching end.
        """
        # Check if no movies are in the playlist and return nothing.
        if len(self._movies) == 0:
            return None
        # Start Random movie
        if self._is_random:
            self._index = random.randrange(0, len(self._movies))
        else:
            # Start at the first movie and increment through them in order.
            if self._index is None:
                self._index = 0
                self._new_iteration = True
            else:
                self._index += 1
            # Wrap around to the start after finishing.
            if self._index >= len(self._movies):
                self._index = 0
	
	if self.is_on_schedule(self._index):
           return self._movies[self._index]

	else:
	   movie_found= False
           movies_nr =  len(self._movies)
	   while movies_nr >=0:
	     movies_nr -= 1
	     self._index += 1
             if self._index >= len(self._movies):
               self._index = 0
               self._new_iteration = True
	     if self.is_on_schedule(self._index):
               movie_found= True;
	       break;

	   if movie_found:
             return self._movies[self._index]
	   else:
	     return None;

    def get_current_index(self):
        # Get current index in the playlist. 
        # Check if no movies are in the playlist and returns nothing if so.
        if len(self._movies) == 0:
            return -1
        else:
            return self._index 

    def is_new_iteration(self):
        """Returns True if just started a new playlist iteration. """
        return self._new_iteration

    def reset_new_iteration(self):
        """Resets  _new_iteration flag. """
        self._new_iteration = False

    def whats_next(self):
        """Get the next movie in the playlist NO INCREMENT for self._index. Will loop to start of playlist
           after reaching end.
           This function is mostly used to paint next image in background to reduce black screen time between movies
        """
        # Check if no movies are in the playlist and return nothing.
        if len(self._movies) == 0:
            return None
        # Start Random movie
        if self._is_random:
           return None
        if self._index is None:
           return None

        nextIndex=self._index+1

        if nextIndex >= len(self._movies):
           nextIndex = 0

        if self.is_on_schedule(nextIndex):
           return self._movies[nextIndex]
        else:
           movie_found= False
           movies_nr =  len(self._movies)
           while movies_nr >=0:
             movies_nr -= 1
             nextIndex += 1
             if nextIndex >= len(self._movies):
               nextIndex = 0
             if self.is_on_schedule(nextIndex):
               movie_found= True;
               break;

           if movie_found:
             return self._movies[nextIndex]
           else:
             return None;

    def length(self):
        """Return the number of movies in the playlist."""
        return len(self._movies)

    def onlyOneActive(self):
        """Returns True if only one movie is active in playlist.
           This is used for setting loop flag when the only one active item in playlist is a movie.
        """
        activeCnt=0
        for i in range(len(self._movies)):
           if self.is_on_schedule(i):
              activeCnt += 1
              if activeCnt >= 2:
                 break
        if activeCnt == 1:
           return True
        else: 
           return False

    def set_prev_index(self):
        """This is used when user wants to navigate back through playlist using Left Arrow Key
	   to calculate previous active position in playlist.
        """
        playlistLength = len(self._movies)
        if playlistLength == 0:
            return None

        # Start Random movie
        if self._is_random:
            return None

        if self._index is None:
            return None        

        currentIndex = self._index
        if playlistLength == 1:
	    return None;

        if playlistLength == 2 and  currentIndex == 0:
             self._index = 1
             return self._movies[0]

        if playlistLength == 2 and  currentIndex == 1:
             self._index = 0;
             return self._movies[1]

        if playlistLength > 2:
                prevIndex = currentIndex-1
                if prevIndex < 0:
                    prevIndex = len(self._movies)-1;

                if self.is_on_schedule(prevIndex):
                    prev2Index = prevIndex-1;
                    if prev2Index < 0 :
                        self._index = len(self._movies)-1
                    else:
                        self._index = prev2Index
                        return self._movies[self._index]

                else:
                    movie_found= False
                    movies_nr =  len(self._movies)
                    while movies_nr >=0:
                       movies_nr -= 1
                       prevIndex -= 1
                       if prevIndex < 0:
                            prevIndex = len(self._movies)-1
                       if self.is_on_schedule(prevIndex):
                           movie_found= True;
                           break;

                    if movie_found:
                       prev2Index = prevIndex-1;
                       if prev2Index < 0 :
                          self._index = len(self._movies)-1
                       else:
                          self._index = prev2Index
                       return self._movies[self._index]
                    else:
                       return None;
