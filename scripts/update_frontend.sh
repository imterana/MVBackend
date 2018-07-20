#! /bin/sh

. scripts/config

mkdir "$BACKEND_TEMPLATE_DIR/"

cd $FRONTEND_DIR;
npm run build &&
cd $BACKEND_DIR &&
cp "$FRONTEND_BUILD_DIR/index.html" "$BACKEND_TEMPLATE_DIR/" &&
cp -r "$FRONTEND_BUILD_DIR/static" "$BACKEND_STATIC_PARENT_DIR";

rm -r $FRONTEND_BUILD_DIR;
