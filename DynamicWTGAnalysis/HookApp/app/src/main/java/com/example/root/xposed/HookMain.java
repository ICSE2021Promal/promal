package com.example.root.xposed;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.callbacks.XC_LoadPackage.LoadPackageParam;

import com.example.root.xposed.hook.HookBothMenus;
import com.example.root.xposed.hook.HookDispatchTouchEvent;
import com.example.root.xposed.hook.HookDialogShow;
import com.example.root.xposed.hook.HookKeyEvent;
import com.example.root.xposed.hook.HookLongClickCallback;

public class HookMain implements IXposedHookLoadPackage {

    @Override
    public void handleLoadPackage(final LoadPackageParam lpparam) {

        String pkg = lpparam.packageName;

        // Hook keyevent operation
        try {
            if (lpparam.packageName.equals("android")) {
                HookKeyEvent.init(lpparam);
            }
        } catch (Error e1) {
            XposedBridge.log("Error:" + e1 + " from key event injection at package:" + lpparam.packageName);
        } catch (Exception e) {
            XposedBridge.log("Exception:" + e + " from key event injection at package:" + lpparam.packageName);
        }

        if (!Utils.PRE_INSTALLED.contains("package:"+pkg+"\n")) {
            XposedBridge.log("Hook Loaded App:" + pkg);
            HookDispatchTouchEvent.init(lpparam);
            HookLongClickCallback.init(lpparam);
            HookBothMenus.init(lpparam);
            HookDialogShow.init(lpparam);
            }
    }
}
