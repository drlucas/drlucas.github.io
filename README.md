For skelly!

On a PC - load up the https://drlucas.github.io/skellyindex.html website - thats how you upload audio to it I think
then the skelly.py file is what goes onto the FPP server 

The Chrome page (or the official app) is for loading content onto the skelly. You upload the audio files (the page can convert MP3s for you), and you can set eye icons, colors and movement for each one. The files live in the skelly’s own memory and get numbered 1, 2, 3 and so on. The page’s “Files on Device” list shows those numbers.
skelly.py is the trigger. It connects over Bluetooth and tells the skelly to play file number N, where N is the argument. FPP runs it from a playlist at the right moment in your show.

You can do the uploading with the official app instead. Some people use the Chrome page because it allows MP3 uploads and files longer than 30 seconds, though the page itself warns that longer tracks are experimental.

Why the web page might still fail. You connected with the official app, so the skelly is working and reachable, but the Chrome page still failed. That points to the browser side rather than the skelly. Two things to check:

Close the official app completely before trying the page, because the skelly accepts only one connection at a time.
Use Chrome or Edge on desktop, or Chrome on Android. iPhone browsers can’t do Web Bluetooth.

If the page still won’t connect, tell me what shows in its Log panel when you click Connect.

Before moving to FPP, find out which file number is which. Once your files are uploaded, note their numbers, then test from the Pi with python3 skelly.py 1, python3 skelly.py 2, and so on. If the right audio plays each time, you can drop the same numbers into your FPP playlist entries.
