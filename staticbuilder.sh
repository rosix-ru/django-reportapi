#!/usr/bin/env bash

if [ -f 'reportapi/__init__.py' ]
then
    VERSION=$(python -c 'import reportapi; print(reportapi.get_version());');
else
    echo 'This script must be run from it directory!';
    exit 1;
fi;


echo "ReportAPI version: ${VERSION}";
echo '';

SRC_DIR="reportapi/static_src";
DST_DIR="reportapi/static/reportapi";

VERSION_DIR="${DST_DIR}/${VERSION}";
CSS_DIR="${VERSION_DIR}/css";
JS_DIR="${VERSION_DIR}/js";
IMG_DIR="${VERSION_DIR}/img";

rm -R ${DST_DIR}
mkdir -p ${CSS_DIR} ${JS_DIR} ${IMG_DIR};

# CSS
echo "STARTS THE CREATION OF CSS FILES";
echo '';

cp ${SRC_DIR}/css/reportapi.css ${CSS_DIR}/reportapi.css;
echo "copied ${CSS_DIR}/reportapi.css";

yui-compressor ${CSS_DIR}/reportapi.css \
            -o ${CSS_DIR}/reportapi.min.css --charset "utf-8";
echo "created ${CSS_DIR}/reportapi.min.css";
echo '';

# JS
echo "STARTS THE CREATION OF JS FILES";
echo '';

cp ${SRC_DIR}/js/reportapi.js ${JS_DIR}/reportapi.js;
echo "copied ${JS_DIR}/reportapi.js";

yui-compressor ${JS_DIR}/reportapi.js \
            -o ${JS_DIR}/reportapi.min.js --charset "utf-8";
echo "created ${JS_DIR}/reportapi.min.js";
echo '';

# IMG
echo "STARTS THE COPYING IMAGE FILES";
echo '';

#~ cp ${SRC_DIR}/img/*.ico ${IMG_DIR}/;
#~ cp ${SRC_DIR}/img/*.jpg ${IMG_DIR}/;
cp -v ${SRC_DIR}/img/*.png ${IMG_DIR}/;
cp -v ${SRC_DIR}/img/*.svg ${IMG_DIR}/;

echo '';

echo "ALL COMPLETED";

exit 0;
