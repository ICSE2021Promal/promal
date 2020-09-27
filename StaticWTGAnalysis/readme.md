# StaticWTGAnalysis

The first step of Promal is to obtain Window Transition Graph(WTG) using static analysis. We use the state-of-the-art tool **GATOR** to do so. **GATOR** is also used to collect view trees for the window transition prediction module.

## Introduction

This folder contains a copy of **GATOR** and the scripts to run it.
+ `gatorPromal/run_gator.py`: Run gator and collect WTG or view tree.
+ `gatorPromal/gather_xml`: Collects XML files after running gator for view tree.

## Requirements

+ Python>=3.6.9
+ JDK Version: 1.8.0_265

## Usage

First, navigate to `./gatorPromal`.

Run the script:

```bash
    python3 run_gator.py --apk_dir <APK_DIR> --adk_dir <ANDROID_SDK_DIR> --mode <"wtg"|"viewtree">
```
If in "wtg" mode, the results will be written to `dot_output`.

If in "viewtree" mode, run `gather_xml.sh` afterwards and the results will be written to `xml_output`.