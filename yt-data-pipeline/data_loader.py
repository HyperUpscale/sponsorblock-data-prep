import sqlite3

con = sqlite3.connect("../../../databases/segments.db")

cur = con.cursor()

with open("sponsorTimes.csv") as f:
    line_count = 0
    for text_line in f:
        if line_count % 1600000 == 0:
            print(f"Progress: {line_count/1600000 * 10}%")
        line = text_line.split(",")
        if len(line) > 10:
            if line[10] == "sponsor" and line[0] != "" and int(line[3]) > 1:
                cur.execute(f"INSERT INTO sponsorblock VALUES ('{line[0]}', '{line[1]}', '{line[2]}', '{line[3]}', '{line[10]}', '{line_count}')")
                con.commit()
        else:
            print(f"Skip line {line_count}")
        del text_line, line
        line_count += 1

    