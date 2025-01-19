select TO_VARCHAR(max(time_valid_utc), 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
from onpoint_id.history_hour where country='US'
