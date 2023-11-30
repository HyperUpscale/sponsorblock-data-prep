`data_loader.py` loads in from the original file. This loads to a SQLite database. A full version of the database can be found [here](https://drive.google.com/file/d/1yVCj5w6B0j8wbgC98-C_MtyqRKnOqEEP/view?usp=sharing)

I then run the following command on the SQLite database to get the 1000 videos with the highest minimum vote. This means that even
their least certain mark is pretty certain.

`SELECT video_id, MIN(votes) AS min_votes FROM sponsorblock GROUP BY video_id ORDER BY min_votes DESC LIMIT 1000;`

I copy the video ids from this query to a spreadsheet and append `https://www.youtube.com/watch?v=` to them. I then copy these rows
from the spreadsheet to batch.txt.

The segmenting code, `segmenter.py` iterates through the downloaded transcripts, queries the SponsorBlock markers for the corresponding video, and segments the transcript into segments. These segments are then stored in a new table in the same database. We save this data to a CSV to train our models.
