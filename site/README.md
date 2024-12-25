NG - Web App
===============

Requirements
------------

* [Docker](https://docs.docker.com/get-docker/)


How it Works
------------

With docker compose we run two containers

   * flask: The Flask App
   * mongo: The MongoDB Database


The app will listen in localhost port `5000`
      
* On first run:
  - MongoDB data dir will be created in dir `db` of project root
      
    **The database needs to be initializated acessing http://localhost:5000/init in your browser**

        This will create all User Permission Roles and Estados/Municipios
      
  - Create a Admin User account:

    * **All emails included in `MAIL_ADMIN` var of `.env` file will have admin rights**, create an account with one of these emails to access all functions
          
            You can change the `.env` file with a list of emails separated by "," or use one of the defaults emails (eg `web@boragora.app`)


  - Create a Regular User for development and debugging:

    * If you are developing offline or don't have an email server to send registration email confirmations:
            
      **Always use email accounts in `MAIL_ADMIN` or `MAIL_USERS` var of `.env` file**

            Flask is configured to skip email confirmation for these emails


Steps
-----

1) Clone and `cd` this repository:

    `git clone git@gitlab.com:boragora/ng.git && cd ng`

2) Copy `env-example` file to `.env`:

    `cp env-example .env`

3) Change the `MAIL_ADMIN` and `MAIL_USERS` vars in `.env` file or create account using one of the default emails in Step 6

    `nano .env`

4) Start docker compose services in background:

    `docker compose up -d`

5) Initialize the database if it's the first run:

    ***Go to http://localhost:5000/init in your browser***

6) See (and follow) logs from flask:

    `docker compose logs -f flask`

        Stop pressing "CTRL+C"

7) Open http://localhost:5000/ in your browser.

      The specific authentication page is at http://localhost:5000/auth

      - Create a user account that is in the environment var `MAIL_ADMIN` to access the Dashboard
      

        The Dashboard is at http://localhost:5000/dashboard


8) Flask will always reload when a code changes, if it crashes you can restart the flask container with:


      `docker compose restart flask`


9) Happy coding!



Background Requirements
-----------------------

* Separate Frontend from API





