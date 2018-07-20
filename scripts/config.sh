# Directories
BACKEND_REPO_FOLDER='mvbackend'
BACKEND_DIR=`pwd`;
BACKEND_SCRIPTS_DIR="$BACKEND_DIR/scripts"
BACKEND_TEMPLATE_DIR="$BACKEND_DIR/gunicorn/spa/templates"
BACKEND_STATIC_PARENT_DIR="$BACKEND_DIR/gunicorn/spa"

FRONTEND_REPO_FOLDER='mvfrontend'
FRONTEND_DIR="$BACKEND_DIR/../$FRONTEND_REPO_FOLDER/"
FRONTEND_BUILD_DIR="$FRONTEND_DIR/build"

# API keys
VK_CLIENT=''
VK_SECRET=''
VK_KEY=''
GITHUB_CLIENT=''
GITHUB_SECRET=''
GOOGLE_CLIENT=''
GOOGlE_SECRET=''

# Django superuser
ROOT_USERNAME='root'
ROOT_EMAIL='admin@example.com'
ROOT_PASSWORD='smthsecure'

# Import overriden config values
OVERRIDE_CONFIG_PATH="$BACKEND_SCRIPTS_DIR/config.override.sh"

if [ -e "$OVERRIDE_CONFIG_PATH" ]; then
  . `dirname "$0"`/config.override.sh;
fi;
