#! /bin/bash

. `dirname "$0"`/config.sh

EXECUTE_IN_DOCKER() {
 echo docker exec -it "$BACKEND_REPO_FOLDER""_gunicorn_1" $@;
 docker exec -it "$BACKEND_REPO_FOLDER""_gunicorn_1" "$@";
}

docker-compose up --build -d &&
EXECUTE_IN_DOCKER python wait_for_db.py && 
EXECUTE_IN_DOCKER python manage.py shell -c 'from django.contrib.auth.models import User;
User.objects.create_superuser('\"$ROOT_USERNAME\"', '\"$ROOT_EMAIL\"', '\"$ROOT_PASSWORD\"')' &&

if [ ! -z "$VK_CLIENT" ]; then
  EXECUTE_IN_DOCKER python manage.py register_social_app vk "$VK_CLIENT" "$VK_SECRET" --key "$VK_KEY"
fi &&

if [ ! -z "$GITHUB_CLIENT" ]; then
  EXECUTE_IN_DOCKER python manage.py register_social_app github "$GITHUB_CLIENT" "$GITHUB_SECRET"
fi &&

if [ !  -z "$GOOGLE_CLIENT" ]; then
  EXECUTE_IN_DOCKER python manage.py register_social_app google "$GOOGLE_CLIENT" "$GOOGLE_SECRET"
fi;
