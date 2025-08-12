#!/bin/bash
yarn build
cp ../snaprecommend/static/index.html ../snaprecommend/templates/index.html
rm ../snaprecommend/static/index.html
echo "Build and copy done"
