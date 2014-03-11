#!/usr/bin/env bash

minify() {
    TYPE=$1;
    APP=$2;
    FILE=$3;
    if [ ! $FILE ]; then
        FILE=$APP;
    fi;
    if [ -f "$APP/static_src/$TYPE/$FILE.$TYPE" ];
    then
        yui-compressor -v "$APP/static_src/$TYPE/$FILE.$TYPE" \
            -o "$APP/static_src/$TYPE/$FILE.min.$TYPE" --charset "utf-8";
        echo "CREATE $APP/static_src/$TYPE/$FILE.min.$TYPE";
    fi;
}

minify "css" "reportapi";
minify "js" "reportapi";

