You will need to create an file named config.json with the following content on the root folder:

```json
{
    "MACHADO":{
        "consumer_key" : "CONSUMER KEY",
        "consumer_secret" : "CONSUMER SECRET",
        "access_token_key" : "TOKEN KEY",
        "access_token_secret" : "TOKEN SECRET",
        "database" : "docs\\db.db",
        "models" : ["default.json"],
        "hashtags" : ["quotes"],
        "avoidthose" : ["polit"],
        "favsinrun" : 10
    }
}
```

Put your credentials in the fields, change the lists the values you want for the lists and leave the file in the folder.

You don't need to create a database manually, as sqlite3 will create a database if there isn't one. To make the runbat work, change the lines
set root = C:\Users\JGC\Desktop\Trabalhos\Python\Machadobot
and start C:\Users\JGC\anaconda3\pythonw.exe
to your the locations of the folder on your machine and your python.exe file location.