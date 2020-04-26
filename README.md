You will need to create an file named config.json with the following content:

```json
{
    "MACHADO":{
        "consumer_key" : "CONSUMER KEY",
        "consumer_secret" : "CONSUMER SECRET",
        "access_token_key" : "TOKEN KEY",
        "access_token_secret" : "TOKEN SECRET",
        "database" : "docs\\db.db",
        "model": "models\\default.json"
    }
}
```

Put your credentials in the fields and leave the file in the folder.

Then create a database by running "touch db.db" inside of the docs folder.