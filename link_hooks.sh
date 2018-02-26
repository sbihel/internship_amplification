#!/bin/sh
root_path=`git rev-parse --show-toplevel`
for f in "${root_path}/.githooks"/*; do
    filename="${f##*/}"
    target_path="${root_path}/.git/hooks/$filename"
    ln -s $f $target_path # maybe use -f option
    chmod +x $target_path
done
