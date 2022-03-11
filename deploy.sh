cd frontend/

npm run build

cd ..

set -o allexport

source .env

set +o allexport

heroku container:push web -a=metarkitex-generator --arg secret_key=$SECRET_KEY

heroku container:release -a metarkitex-generator web