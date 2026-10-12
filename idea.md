# The original idea

To cut and isolate voices from videos. The idea is to pick and isolate parts from a single distinct speakers, creating a snippet of 03 to 20 seconds of a speaker, sourced from a link in youtube.  


### First part

The best idea so far is to code a simple script to download audio bits from youtube using yt-dlp, like in this example:

```
yt-dlp -x --audio-format wav --force-keyframes-at-cuts --download-sections "*00:00:03-00:00:15" -o "clovis.wav" "https://www.youtube.com/watch?v=TRPBY_lxJfE"
```

We will need to understand what the yt-dlp library can do first, before we project or build anything.

The ultimate goal is to create a tool with frontend to manage the variables that may interest us in downloading audio snippets. 

Don't forget to ask to define the location of output before downloading it. 

---- 

### Second part

Later, we will need to prepare the .wav extracted audio, to clean it of any artifact and isolate a unique voice from the specific audio. So another tool maybe required. We can research and discuss how we are going to do it. 


### Known Challenges

* The yt-dlp tool define the second from which it will cut the audio, but sometimes to isolate the speech we are interested on, we would need to draw the exact microsecond in which the speech starts, to avoid peaking up artifacts. 

