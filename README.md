# pi_video_looper
Application to turn your Raspberry Pi into a dedicated looping video playback device, good for art installations, information displays, or just playing cat videos all day.

Some new features :
    - displaying JPG and PNG images using only pygame.    
    - possibility to insert an image to be displayed between videos instead of black screen.    
    - if the playlist is composed of video files followed by images, the images will be displayed in the background to optimize loading and transition from one file to another. This also will reduce black screen time between playlist positions.    
    - possibility to limit the display of files by time intervals (date ranges or time intervals within a day).
    - possibility to log feedback about playing process(timestamp, filename, palyerID, etc).    
    - navigation through the playlist (back , forward) using the left or right arrows on keyboard.    
    
    

Things still not working/tested:
    - I think we can no longer use the random order option in the playlist
    - I did not test if these changes work with Hello Video
    - Movies or images cannot be placed in different folders. For the moment content and playlist descriptor file need to stay in the same folder.
    - Without the file playlist.ini (playlist descriptor) nothing works.


Format of playlist line:

    POSITION:=:FILENAME:=:START(%Y%m%d%H%M%S):=:END(%Y%m%d%H%M%S):=:ISTART(%H%M%S):=:IEND(%H%M%S):=:SCREEN_TIME(SECONDS):=:SEND_FEEDBACK(T/F)

    POSITION - position of file in playlist. For the moment is not used can be 0 on all lines.
    FILENAME - position filename
    START(%Y%m%d%H%M%S) - The beginning of the display period (OPTIONAL - if not provided position will be displayed forever)
    END(%Y%m%d%H%M%S) - The end of the display period(OPTIONAL - if not provided position will be displayed forever)
    ISTART(%H%M%S) - The beginning of the day time interval for display (OPTIONAL - if not provided position will be displayed all day)
    IEND(%H%M%S) - The end of the day time interval for display (OPTIONAL - if not provided position will be displayed all day)
    SCREEN_TIME(SECONDS) - The number of seconds to display the current file. This is mainly used for displaying images. For video files is used only for feedback in case of   starting omxplayer with loop flag.
    SEND_FEEDBACK(T/F) - If recording feedback is enabled or not for current file.

    Example:
    1:=:image1.jpg:=:20191003072708:=:20200403072708:=::=::=:15:=:T
    2:=:movie1.mp4:=:20191003145830:=:20200403145830:=::=::=:18:=:F
    3:=:movie2.mp4:=::=::=::=::=:5:=:T
    4:=:image2.jpg:=:20191003072708:=:20200403072708:=::=::=:80:=:T
    5:=:image3.jpg:=:20190927092416:=:20200327092416:=:064000:=:231800:=:15:=:F
    6:=:image2.jpg:=::=::=:064000:=:173000:=:80:=:T





