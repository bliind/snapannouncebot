# snapannouncebot

announcebot.db
```sql
CREATE TABLE posts(
    id TEXT PRIMARY KEY NOT NULL,
    guild INT,
    channel TEXT,
    content TEXT,
    link TEXT,
    datestamp TEXT
);

CREATE TABLE support_message(
    message TEXT
);
INSERT INTO support_message (message) VALUES ('');
```

survey.db
```sql
CREATE TABLE survey(
    guild INT,
    datestamp INT,
    channel_id INT,
    message_id INT,
    expires INT
);

CREATE TABLE survey_response(
    guild INT,
    datestamp INT,
    channel_id INT,
    message_id INT,
    user_id INT,
    response TEXT
);
```
