dependencies:
    pip install qrcode lib
    pip install channels  
    pip install python-dotenv 
    pip install django psycopg2-binary djangorestframework
    pip install virtualenv

instead of using// virtualenv venv
run// python -m virtualenv venv

then bypass script restrictions // Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
then activate environment// .\venv\Scripts\Activate

shortcut: pip install -r requirements.txt
