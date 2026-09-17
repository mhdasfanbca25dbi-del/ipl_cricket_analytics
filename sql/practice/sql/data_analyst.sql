1. Find the top 10 grounds by number of matches

SELECT 
    venue,
    COUNT(DISTINCT match_id) AS match_count
FROM matches
GROUP BY venue
ORDER BY match_count DESC
LIMIT 10;

explaination:
COUNT(DISTINCT match_id) counts the number of unique matches.
GROUP BY venue groups matches by ground.
ORDER BY match_count DESC shows grounds with the highest matches first.
LIMIT 10 gives only the top 10 grounds.

2. Find grounds with an average innings score above 165, using a minimum of 25 matches

SELECT 
    m.venue,
    AVG(i.total_runs) AS average_score,
    COUNT(DISTINCT m.match_id) AS match_count
FROM matches m
JOIN innings i 
    ON m.match_id = i.match_id
GROUP BY m.venue
HAVING COUNT(DISTINCT m.match_id) >= 25
   AND AVG(i.total_runs) > 165
ORDER BY average_score DESC;

Explanation:
JOIN connects matches with innings.
AVG(i.total_runs) calculates the average innings score.
COUNT(DISTINCT match_id) >= 25 ensures the ground has at least 25 matches.
AVG(...) > 165 selects grounds where the average score is above 165.
HAVING is used because we are filtering grouped results.

3. Calculate the chase win percentage for grounds with at least 50 matches

SELECT
    venue,
    COUNT(DISTINCT match_id) AS match_count,
    ROUND(
        100.0 * SUM(CASE 
            WHEN win_type = 'wickets' THEN 1 
            ELSE 0 
        END) / COUNT(DISTINCT match_id),
        2
    ) AS chase_win_percentage
FROM matches
GROUP BY venue
HAVING COUNT(DISTINCT match_id) >= 50
ORDER BY chase_win_percentage DESC;

Explanation:
A win by wickets usually means the team successfully chased the target.
SUM(CASE...) counts the number of chase wins.
Divide chase wins by total matches.
Multiply by 100 to get percentage.
Only grounds with 50 or more matches are included.

4. Count the number of unique cleaned venues

If your cleaned venue column is called cleaned_venue:

Query:
SELECT COUNT(DISTINCT cleaned_venue) AS unique_cleaned_venues
FROM matches
WHERE cleaned_venue IS NOT NULL;

Explanation:
DISTINCT removes duplicate venue names.
COUNT counts the remaining unique venues.
IS NOT NULL ignores missing venue values.

5. Find the five grounds with the lowest powerplay run rate

Assuming the innings table contains powerplay_runs and powerplay_overs.

Query:
SELECT
    m.venue,
    SUM(i.powerplay_runs) / SUM(i.powerplay_overs) AS powerplay_run_rate
FROM matches m
JOIN innings i
    ON m.match_id = i.match_id
GROUP BY m.venue
ORDER BY powerplay_run_rate ASC
LIMIT 5;

Explanation:
SUM(powerplay_runs) gives total powerplay runs at the ground.
SUM(powerplay_overs) gives total powerplay overs.
Dividing them gives the powerplay run rate.
ASC sorts from lowest to highest.
LIMIT 5 gives the five grounds with the lowest rate.

6. Why COUNT(DISTINCT match_id) is safer than COUNT(*) after a JOIN

Example:

SELECT
    m.venue,
    COUNT(DISTINCT m.match_id) AS matches
FROM matches m
JOIN deliveries d
    ON m.match_id = d.match_id
GROUP BY m.venue;

Explanation:

Suppose one match has 120 deliveries.

After joining matches with deliveries, that one match can appear 120 times.

So:

COUNT(*)

could count the same match 120 times.

But:

COUNT(DISTINCT match_id)

counts that match only once.

Therefore, when a JOIN creates multiple rows for the same match, COUNT(DISTINCT match_id) is safer for calculating the number of matches.


7. Why day/night cannot be answered from match_date alone

match_date only tells us which date the match happened.

For example:

2026-04-10

doesn't tell us whether the match started in the morning, afternoon, or evening.

To determine day/night, you need additional information such as:

match_start_time

or a field such as:

day_night

For example:

SELECT
    match_date,
    match_start_time,
    day_night
FROM matches;

Explanation:
Two matches can happen on the same date but have different start times:

match_date	start_time	Type
2026-04-10	15:30	Day
2026-04-10	19:30	Night