package com.pocketapp;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;

import org.kivy.android.PythonActivity;
import org.kivy.android.PythonUtil;

public class SmsReceiver extends BroadcastReceiver {

    private static final String TAG = "PocketSmsReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!android.provider.Telephony.Sms.Intents.SMS_RECEIVED_ACTION
                .equals(intent.getAction())) {
            return;
        }

        Bundle bundle = intent.getExtras();
        if (bundle == null) return;

        Object[] pdus = (Object[]) bundle.get("pdus");
        String format  = bundle.getString("format");
        if (pdus == null) return;

        for (Object pdu : pdus) {
            SmsMessage msg = SmsMessage.createFromPdu((byte[]) pdu, format);
            if (msg == null) continue;

            String sender = msg.getOriginatingAddress();
            String body   = msg.getMessageBody();

            Log.d(TAG, "SMS from: " + sender);

            // Hand off to Python — PythonActivity runs on the main thread
            // so this is safe to call from the receiver thread.
            try {
                PythonActivity.mActivity.runOnUiThread(() -> {
                    try {
                        // Call the global Python function registered by sms_listener.py
                        PythonActivity.mActivity
                            .getClass()
                            .getMethod("on_sms_received", String.class, String.class)
                            .invoke(PythonActivity.mActivity, sender, body);
                    } catch (Exception e) {
                        Log.e(TAG, "Could not call Python callback: " + e.getMessage());
                    }
                });
            } catch (Exception e) {
                Log.e(TAG, "runOnUiThread failed: " + e.getMessage());
            }
        }
    }
}
