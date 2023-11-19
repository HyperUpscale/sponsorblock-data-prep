import sqlite3
import webvtt
import os

# talk about this code in write up

# for each video (load only a few videos at a time - call video id unique and then limit to 1000 at a time or something and after each 1000 call more)

def convert_to_seconds(hh_mm_ss_dd_string):
    decimal_split_out = hh_mm_ss_dd_string.split('.')
    seconds = float("0." + decimal_split_out[1])
    hh_mm_ss_split = decimal_split_out[0].split(":")
    seconds += float(hh_mm_ss_split[2])
    seconds += float(hh_mm_ss_split[1]) * 60.0
    seconds += float(hh_mm_ss_split[0]) * 3600.0

    return seconds

def clean_vtt(text):
    clean_text = "WEBVTT\nKind: captions\nLanguage: en\n\n"
    last_main_line = ""
    for line in text:
        if "-->" in line:
            last_main_line = line
        if "<" in line:
            clean_text += last_main_line + line + "\n"
    return clean_text

def write_segments(video_id, caption_file, segment_timestamps, db_connection):
    '''
    Writes segments to a db. Segment timestamps should be a list of tuples of the form
    (end_timestamp, segment_label). A segment is presumed to run from the end_timestamp
    of the previous segment to the end_timestamp of the this segment. That is, the end
    timestamp of the segment is the start_timestamp of the next segment. This ensures
    that the entire transcript falls into a segment. The first element has an start timestep of 0.

    The segmenter works at the granularity of the input file. The segmenter does not break up
    units created in the vtt. An entire unit is added to a segment if the unit starts within the segment.
    '''
    cursor = db_connection.cursor()
    with open(caption_file, "r+") as f:
        cleaned_captions = clean_vtt(f.readlines())
    with open("temp.vtt", "w+") as f:
        f.write(cleaned_captions)
    vtt = webvtt.read("temp.vtt")
    current_segment_transcript = ""
    current_segment_count = 0

    for caption in vtt:
        segment_end, segment_label = segment_timestamps[current_segment_count]

        current_segment_transcript += caption.text + " "
        
        if convert_to_seconds(caption.start) > segment_end:
            # This is the last caption in this segment.
            # Write segment to database and start new segment
            cursor.execute(f'INSERT INTO segments VALUES ("{video_id}", "{current_segment_count}", "{segment_label}", "{current_segment_transcript}")')
            db_connection.commit()
            del current_segment_transcript
            current_segment_transcript = ""
            current_segment_count += 1

    if current_segment_transcript != "":
        cursor.execute(f'INSERT INTO segments VALUES ("{video_id}", "{current_segment_count}", "{segment_label}", "{current_segment_transcript}")')
        db_connection.commit()
        del current_segment_transcript
        current_segment_transcript = ""

    del cursor

    os.remove("temp.vtt")

def extract_times(ad_start_end_times):
    '''
    Converts a list of ad start and end times (a list where each item corresponds
    to an ad and is a tuple of start time and end time) into a list of overall segment times
    where each segment (ad or not) is represented by a tuple
    of end_time and label. The last element correponds to the
    segment that runs to the end but is labeled with an end
    time of INF as video end times are not recorded in the
    sponsorblock dataset.
    '''
    blocks = []
    last_open_block = 0.0
    for ad_start, ad_end in ad_start_end_times:
        if ad_start > last_open_block:
            blocks.append((float(ad_start), "non-sponsor"))
        if ad_start < last_open_block:
            # Ad is not mutually exclusive. Ignore
            continue
        blocks.append((float(ad_end), "sponsor"))
        last_open_block = ad_end
    blocks.append((float("inf"), "non-sponsor"))
    return blocks

subtitle_files = os.listdir("../subtitles")

con = sqlite3.connect("../../../databases/segments.db")

cur = con.cursor()

i = 0

for subtitle_file in subtitle_files:
    i += 1
    video_id = subtitle_file.split(".")[0]
    start_end_times = cur.execute(f"SELECT start_time, end_time FROM sponsorblock WHERE video_id='{video_id}' ORDER BY start_time ASC")
    blocks = extract_times(start_end_times)
    try:
        write_segments(video_id, "../subtitles/" + subtitle_file, blocks, con)
    except:
        print(f"{video_id} failed")
    if i % 100 == 0:
        print(f"{10 * i/100}%")