# Alone Bot
A personal bot made for discord.

## Running your own version

0. **Note**

Please take all code from the stable release, also known as the stable branch. I upload a lot of broken code and have to fix it through testing so a version you download from anywhere other than stable might be unstable. Thanks!


1. **Install Python 3.9 or higher**

You need this for the bot to actually run.
For windows, you can get it from the microsoft store or the official [python website](https://www.python.org/).

On GNU/Linux, you can run apt install python, or whatever your desired package manager is.

On Mac, you can download the installer from the website, referenced above.


2. **Setup a virtual environment (optional)**

I personally don't use because its the only thing i run, but if you have multiple bots/projects at the same time, i recommend using one.

Just do `python -m venv venv`


3. **Install the requirements**

The easiest way is just to `pip install -Ur requirements.txt`.
You can also install them manually, or other versions that you specifically want.


4. **Create a database in PostgreSQL**

You will need PostgreSQL 14 or higher.

Make your own database however you like it and then run the following command:

```psql -d databasename -a -f schema.sql```


5. **Setup your .env config**

Make a .env file, just like the example.env.
You can also just change the values in the example.env and change the name from example.env to .env


6. **All done!**

Now, just run main.py and everything should work! ..hopefully!
