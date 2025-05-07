#!/usr/bin/env sh
set -e

# 清空旧的 .git 文件夹
rm -rf docs/.git/

# 进入 docs 目录并初始化 Git
cd docs
git init
git add -A
git commit -m "deploy $(date)"

# 强制推送到 gh-pages 分支
git push -f git@github.com:YyyyyyiZ/AHD4Inventory.git master:gh-pages