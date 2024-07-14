# snapannouncebot

announcebot.db
```sql
CREATE TABLE posts(
    id TEXT PRIMARY KEY NOT NULL,
    channel TEXT,
    content TEXT,
    link TEXT,
    datestamp TEXT
);
```

survey.db
```sql
CREATE TABLE survey(
    datestamp INT,
    channel_id INT,
    message_id INT,
    expires INT
);

CREATE TABLE survey_response(
    datestamp INT,
    channel_id INT,
    message_id INT,
    user_id INT,
    response TEXT
);
```
