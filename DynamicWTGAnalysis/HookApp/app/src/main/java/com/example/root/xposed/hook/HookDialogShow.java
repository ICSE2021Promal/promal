package com.example.root.xposed.hook;

import android.app.ActivityManager;
import android.app.AndroidAppHelper;
import android.app.Dialog;
import android.content.ComponentName;
import android.content.Context;
import android.widget.Adapter;
import android.widget.ListView;

import java.util.ArrayList;
import java.util.List;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

import static com.example.root.xposed.Utils.getOutput;
import static com.example.root.xposed.Utils.getStack;
import static com.example.root.xposed.Utils.getTimeStamp;
import static de.robv.android.xposed.XposedHelpers.findAndHookMethod;

public class HookDialogShow {
    public static void init(final XC_LoadPackage.LoadPackageParam lpparam){
        try {
            findAndHookMethod(
                "android.app.Dialog",
                lpparam.classLoader,
                "show",
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param)
                            throws Throwable {
                        String pkg = lpparam.packageName;
                        String TAG = getTimeStamp();

                        Dialog dialog = (Dialog) param.thisObject;
                        List outputs = new ArrayList();

                        Context context = (Context) AndroidAppHelper.currentApplication();
                        ActivityManager am = (ActivityManager) context.getSystemService(context.ACTIVITY_SERVICE);
                        ComponentName cn = am.getRunningTasks(1).get(0).topActivity;

                        outputs.add(pkg);
                        outputs.add("Dialog");
                        outputs.add(TAG);
                        outputs.add("SourceActivity:" + cn.getClassName());
                        try {
                            String title = (String) XposedHelpers.getObjectField(XposedHelpers.getObjectField(dialog,"mAlert"),"mTitle");
                            outputs.add("Title:"+title);
                        } catch (Error e){ }catch (Exception e){ }
                        try {
                            String title = (String) XposedHelpers.getObjectField(XposedHelpers.getObjectField(dialog,"title"),"mText");
                            outputs.add("Title:"+title);
                        } catch (Error e){ }catch (Exception e){ }
                        try {
                            ListView listview = (ListView) XposedHelpers.getObjectField(XposedHelpers.getObjectField(dialog,"mAlert"),"mListView");
                            Adapter adapter = listview.getAdapter();
                            outputs.add("List:"+XposedHelpers.getObjectField(adapter,"mObjects").toString());
                        } catch (Error e){ }catch (Exception e){ }

                        Throwable ex = new Throwable();
                        String[] stacks = getStack(ex);

                        String stackstr = "Stacks:";
                        for (int i = 0; i < stacks.length; i++) {
                            stackstr = stackstr + stacks[i] + "\t";
                        }
                        outputs.add(stackstr.substring(0,stackstr.length()-1));

                        if (!stackstr.contains("ContextMenuBuilder")){
                            getOutput(outputs);
                        }
                    }
                });
        } catch (Error e){ }catch (Exception e){ }
    }
}
