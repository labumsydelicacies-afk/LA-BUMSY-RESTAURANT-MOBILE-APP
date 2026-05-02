from datetime import datetime
from typing import List

def _get_base_html(content: str) -> str:
    year = datetime.now().year
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9fafb; color: #1f2937;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); max-width: 600px; margin: 0 auto; border: 1px solid #f3f4f6;">
                        <!-- Header -->
                        <tr>
                            <td style="background-color: #e8220a; padding: 30px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 900; letter-spacing: 2px;">LA BUMSY</h1>
                                <p style="color: #fef3c7; margin: 5px 0 0 0; font-size: 14px; font-weight: 600; letter-spacing: 1px;">DELICACIES</p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                {content}
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #fef3c7; padding: 24px; text-align: center; border-top: 1px solid #fde68a;">
                                <p style="margin: 0; color: #b45309; font-size: 14px; font-weight: 700;">Fresh & Delicious, Delivered to You.</p>
                                <p style="margin: 8px 0 0; color: #d97706; font-size: 12px;">© {year} La Bumsy Delicacies. All rights reserved.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def get_verification_otp_html(otp: str, purpose: str) -> str:
    content = f"""
        <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 20px;">Your {purpose.capitalize()} Code</h2>
        <p style="margin: 0 0 24px 0; font-size: 15px; color: #4b5563; line-height: 1.5;">
            Please use the verification code below to complete your {purpose}. This code is valid for 10 minutes.
        </p>
        <div style="background-color: #fef3c7; border-radius: 12px; padding: 24px; text-align: center; border: 1px dashed #f59e0b; margin-bottom: 24px;">
            <p style="margin: 0; font-size: 12px; font-weight: 700; color: #b45309; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">VERIFICATION CODE</p>
            <p style="margin: 0; font-size: 36px; font-weight: 900; color: #d97706; letter-spacing: 4px;">{otp}</p>
        </div>
        <p style="margin: 0; font-size: 14px; color: #6b7280; text-align: center;">
            If you didn't request this code, you can safely ignore this email.
        </p>
    """
    return _get_base_html(content)


def get_delivery_otp_html(order_id: int, otp: str) -> str:
    content = f"""
        <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 20px;">Order #{order_id} is on the way! 🚚</h2>
        <p style="margin: 0 0 24px 0; font-size: 15px; color: #4b5563; line-height: 1.5;">
            Your delicious food has been picked up by our rider and is heading to your location right now.
        </p>
        <div style="background-color: #ecfeff; border-radius: 12px; padding: 24px; text-align: center; border: 1px dashed #06b6d4; margin-bottom: 24px;">
            <p style="margin: 0; font-size: 12px; font-weight: 700; color: #155e75; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">DELIVERY CONFIRMATION CODE</p>
            <p style="margin: 0; font-size: 36px; font-weight: 900; color: #0891b2; letter-spacing: 4px;">{otp}</p>
        </div>
        <p style="margin: 0; font-size: 15px; color: #4b5563; line-height: 1.5; font-weight: 600; text-align: center; background-color: #f3f4f6; padding: 16px; border-radius: 8px;">
            Please provide this code to the rider when they arrive to confirm you've received your order.
        </p>
    """
    return _get_base_html(content)


def get_payment_receipt_html(order_id: int, amount: float, items: list) -> str:
    # items should be a list of objects with food_name, quantity, and price attributes
    
    items_html = ""
    for item in items:
        food_name = item.food_name if hasattr(item, 'food_name') and item.food_name else f"Item #{item.food_id}"
        item_total = item.quantity * item.price
        items_html += f"""
        <tr>
            <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; color: #374151;">
                <span style="font-weight: 600; color: #e8220a; margin-right: 8px;">x{item.quantity}</span> 
                {food_name}
            </td>
            <td align="right" style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; font-weight: 600; color: #111827;">
                ₦{item_total:,.2f}
            </td>
        </tr>
        """

    content = f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 60px; height: 60px; background-color: #dcfce7; border-radius: 50%; color: #16a34a; font-size: 28px; margin-bottom: 16px;">
                ✓
            </div>
            <h2 style="margin: 0 0 8px 0; color: #111827; font-size: 24px;">Payment Successful!</h2>
            <p style="margin: 0; font-size: 15px; color: #6b7280;">Thank you for your order, your payment has been confirmed.</p>
        </div>

        <div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; margin-bottom: 24px;">
            <div style="background-color: #f9fafb; padding: 16px 20px; border-bottom: 1px solid #e5e7eb;">
                <p style="margin: 0; font-weight: 700; color: #374151; font-size: 14px;">ORDER #{order_id}</p>
            </div>
            <div style="padding: 20px;">
                <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 15px;">
                    {items_html}
                    <tr>
                        <td style="padding-top: 16px; font-weight: 600; color: #4b5563;">Total Paid</td>
                        <td align="right" style="padding-top: 16px; font-weight: 800; color: #e8220a; font-size: 18px;">
                            ₦{amount:,.2f}
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        
        <p style="margin: 0; font-size: 14px; color: #6b7280; text-align: center;">
            Your order is now being prepared. We will notify you once it's ready!
        </p>
    """
    return _get_base_html(content)


def get_standard_notification_html(title: str, message: str) -> str:
    content = f"""
        <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 20px;">{title}</h2>
        <p style="margin: 0; font-size: 15px; color: #4b5563; line-height: 1.6; white-space: pre-wrap;">{message}</p>
    """
    return _get_base_html(content)
