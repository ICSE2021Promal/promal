#! /bin/sh

# change ADK to Android sdk location
export ADK=/home/hlwang/sdk

# change GatorRoot to the path of gator
export GatorRoot=/home/hlwang/gator-server
appDir="/home/hlwang/diandian_apk"
var=1

rm -rf output
echo "cleaned output directory"

rm -rf dot_output
echo "cleaned dot_output directory"

mkdir output
mkdir dot_output

for app in `ls $appDir/*.apk`
do
echo "analyzing $app"

python3 AndroidBench/runGatorOnApk.py $app -client WTGDemoClient
echo "done analyzing $app"
var=$((var+1))
done
echo "analyzed $var files"
