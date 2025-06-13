login email : user@gmail.com
password :  password

--------------------------------------------------------------------------------------------------------------------------------------------
Terminal 1: scripts
	venv\Scripts\Activate.ps1
	cd scrpts
	python .\etl_shopify.py

Terminal 2: backend
 	venv\Scripts\Activate.ps1
  	cd backend
	 python manage.py runserver 0.0.0.0:8000

Terminal 3: frontend
 	venv\Scripts\Activate.ps1
	cd frontend
		npm install # if you have created a new venv, else skip this line
	npm start

Terminal 4 (optional): database queries

	psql -U myuser -d mydatabase   (password: login)
