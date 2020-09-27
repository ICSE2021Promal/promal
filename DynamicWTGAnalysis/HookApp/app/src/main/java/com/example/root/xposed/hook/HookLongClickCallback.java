package com.example.root.xposed.hook;

import android.view.View;

import com.example.root.xposed.Utils;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public class HookLongClickCallback {
    public static void init(final XC_LoadPackage.LoadPackageParam lpparam){
        final String pkg = lpparam.packageName;
//        XposedBridge.hookAllMethods(AdapterView.class, "setOnItemLongClickListener", newSetOnItemLongClickListener);
//        XposedBridge.hookAllMethods(View.class, "setOnLongClickListener", newSetOnLongClickListener);
        XposedHelpers.findAndHookMethod(
                "android.widget.AbsListView",
                lpparam.classLoader,
                "performLongPress",
                View.class,
                int.class,
                long.class,
                new XC_MethodHook() {

                    @Override
                    protected void afterHookedMethod(MethodHookParam param)
                            throws Throwable {
                        if (param.getResult().equals(true)){
                            Utils.outputLongClick((View)param.args[0],pkg);
                        }
                    }
                }
        );
    }

//    public static XC_MethodHook newSetOnItemLongClickListener = new XC_MethodHook() {
//
//        @Override
//        protected void beforeHookedMethod(MethodHookParam param) throws Throwable{
//            final ListView.OnItemLongClickListener listener = (ListView.OnItemLongClickListener) param.args[0];
//
//            ListView.OnItemLongClickListener newListener = new ListView.OnItemLongClickListener() {
//                @Override
//                public boolean onItemLongClick(AdapterView parent, View view, int position, long id) {
//                    Utils.writeToLog("Event:LongClick");
//
//                    if (listener == null) {
//                        return false;
//                    } else {
//                        return listener.onItemLongClick(parent, view, position, id);
//                    }
//                }
//
//            } ;
//            param.args[0] = newListener;
//        }
//    };
//
//    public static XC_MethodHook newSetOnLongClickListener = new XC_MethodHook() {
//
//        @Override
//        protected void beforeHookedMethod(MethodHookParam param) throws Throwable{
//            super.beforeHookedMethod(param);
//            final View.OnLongClickListener listener = (View.OnLongClickListener) param.args[0];
//            View.OnLongClickListener newListener = new View.OnLongClickListener() {
//                @Override
//                public boolean onLongClick(View v) {
//                    Utils.writeToLog("Event:LongClick");
//
//                    if (listener == null) {
//                        return false;
//                    } else {
//                        return listener.onLongClick(v);
//                    }
//                }
//
//            } ;
//            param.args[0] = newListener;
//        }
//    };
}
