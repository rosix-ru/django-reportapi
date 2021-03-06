#!/usr/bin/env bash
#
#   Copyright 2014-2015 Grigoriy Kramarenko <root@rosix.ru>
#
#   This file is part of ReportAPI.
#
#   ReportAPI is free software: you can redistribute it and/or
#   modify it under the terms of the GNU Affero General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.
#
#   ReportAPI is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public
#   License along with ReportAPI. If not, see
#   <http://www.gnu.org/licenses/>.
#


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

CSS_SYM="../../static_src/css";
JS_SYM="../../static_src/js";
IMG_SYM="../../static_src/img";

VERSION_DIR="${DST_DIR}/${VERSION}";
CSS_DIR="${VERSION_DIR}/css";
JS_DIR="${VERSION_DIR}/js";
IMG_DIR="${VERSION_DIR}/img";

rm -R ${DST_DIR}
mkdir -p ${CSS_DIR} ${JS_DIR} ${IMG_DIR};

# symlinks for develop dirs
echo 'SYMLINKS FOR DEVELOP DIRS';
cd ${DST_DIR};
ln -s ${CSS_SYM} css;
ln -s ${JS_SYM} js;
ln -s ${IMG_SYM} img;
cd -;
echo '';


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
