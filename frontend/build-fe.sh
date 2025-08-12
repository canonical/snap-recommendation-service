#!/bin/bash
yarn build
mv ../snaprecommend/static/index.html ../snaprecommend/templates/index.html
echo "Done"
