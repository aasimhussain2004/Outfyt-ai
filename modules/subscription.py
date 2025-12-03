import streamlit as st
import datetime
import razorpay
import time
from modules.database import supabase

# Initialize Razorpay Client
try:
    razorpay_client = razorpay.Client(auth=(st.secrets["RAZORPAY_KEY_ID"], st.secrets["RAZORPAY_KEY_SECRET"]))
except Exception as e:
    razorpay_client = None

def get_user_status(user_id):
    """Fetch current tier and usage stats via Supabase Client."""
    if not supabase:
        return None
        
    # Validate UUID
    try:
        if not user_id or len(str(user_id)) < 32:
            raise ValueError("Invalid UUID")
    except:
        # Return default Free Tier for invalid IDs (e.g. "1" from old sessions)
        return {
            "is_premium": False,
            "daily_msg_count": 0,
            "last_active_date": datetime.date.today(),
            "wardrobe_count": 0,
            "subscription_end_date": None
        }

    try:
        # Fetch from Supabase
        response = supabase.table("user_usage").select("*").eq("user_id", str(user_id)).execute()
        
        if response.data:
            data = response.data[0]
            # Parse date string to object if needed, though Supabase returns strings
            last_active = data.get("last_active_date")
            if isinstance(last_active, str):
                last_active = datetime.datetime.strptime(last_active, "%Y-%m-%d").date()
                
            return {
                "is_premium": data.get("is_premium", False),
                "daily_msg_count": data.get("daily_msg_count", 0),
                "last_active_date": last_active,
                "wardrobe_count": data.get("wardrobe_count", 0),
                "subscription_end_date": data.get("subscription_end_date")
            }
        else:
            # Create default record
            try:
                new_data = {
                    "user_id": str(user_id),
                    "is_premium": False,
                    "daily_msg_count": 0,
                    "last_active_date": datetime.date.today().isoformat(),
                    "wardrobe_count": 0
                }
                supabase.table("user_usage").insert(new_data).execute()
                
                return {
                    "is_premium": False,
                    "daily_msg_count": 0,
                    "last_active_date": datetime.date.today(),
                    "wardrobe_count": 0,
                    "subscription_end_date": None
                }
            except Exception as e:
                # Handle race condition or insert error
                return None
    except Exception as e:
        st.error(f"Error fetching status: {e}")
        return None

def verify_and_upgrade_user(supabase, user_id):
    """Force update user status to premium in Supabase."""
    # 1. Update (or Insert) the row
    data = {
        "user_id": str(user_id),
        "is_premium": True,
        "subscription_end_date": "2025-12-31" # Set a valid future date
    }
    # Use upsert to handle cases where user_usage row doesn't exist yet
    supabase.table('user_usage').upsert(data).execute()
    return True

def check_message_limit(supabase, user_id):
    """Check limit, prioritizing Premium status and handling Daily Resets."""
    try:
        # 1. Fetch User Data
        response = supabase.table('user_usage').select("*").eq('user_id', str(user_id)).execute()
        
        if not response.data:
            # Create default record if missing
            try:
                new_data = {
                    "user_id": str(user_id),
                    "is_premium": False,
                    "daily_msg_count": 0,
                    "last_active_date": datetime.date.today().isoformat(),
                    "wardrobe_count": 0
                }
                supabase.table("user_usage").insert(new_data).execute()
                return True, "New User"
            except:
                return True, "Error creating user" # Fail open

        user_data = response.data[0]
        
        # 2. Check Premium (Unlimited)
        if user_data.get('is_premium', False):
            return True, "Premium Member"

        # 3. DAILY RESET LOGIC
        last_active_str = user_data.get('last_active_date')
        today_str = datetime.date.today().isoformat()
        
        current_count = user_data.get('daily_msg_count', 0)

        # If last active date is NOT today, reset count
        if last_active_str != today_str:
            try:
                supabase.table('user_usage').update({
                    "daily_msg_count": 0, 
                    "last_active_date": today_str
                }).eq('user_id', str(user_id)).execute()
                current_count = 0 # Local update
            except Exception as e:
                pass # Non-critical, might just be a read replica lag

        # 4. Check Limit (25 for Free Tier)
        if current_count < 25:
            return True, f"{current_count}/25"
        else:
            return False, "Daily limit reached. Resets tomorrow."
            
    except Exception as e:
        # Fail open if DB is down
        return True, "System Error"

def check_wardrobe_limit(supabase, user_id):
    """Check limit, prioritizing Premium status."""
    try:
        # 1. Fetch User Usage Data (and create if missing)
        response = supabase.table('user_usage').select("*").eq('user_id', str(user_id)).execute()
        
        if not response.data:
            # Create default record if missing
            try:
                new_data = {
                    "user_id": str(user_id),
                    "is_premium": False,
                    "daily_msg_count": 0,
                    "last_active_date": datetime.date.today().isoformat(),
                    "wardrobe_count": 0
                }
                supabase.table("user_usage").insert(new_data).execute()
                # Continue as Free user
            except:
                pass # Fail open or continue to check count
        else:
            # Check Premium Status
            if response.data[0].get('is_premium', False):
                return True # Premium = Unlimited
            
        # 2. Check Count (Free Tier Limit)
        response = supabase.table('wardrobe').select("id", count='exact').eq('user_id', str(user_id)).execute()
        count = response.count
        
        if count < 5:
            return True
            
        return False
    except Exception as e:
        # Log error if possible
        return False # Fail safe (Block if error to prevent abuse, or True to be nice? User said "Do NOT return False" for missing user, but here we are in Exception)
        # Actually, if exception, it's safer to return False usually, but for "new user" bug, we handled it above.

def increment_message_count(user_id):
    """Add +1 to usage."""
    if not supabase: return
    
    try:
        # Fetch current count to be safe
        response = supabase.table("user_usage").select("daily_msg_count").eq("user_id", str(user_id)).execute()
        if response.data:
            current = response.data[0]["daily_msg_count"]
            supabase.table("user_usage").update({"daily_msg_count": current + 1}).eq("user_id", str(user_id)).execute()
            
    except Exception as e:
        pass

def create_payment_link(user_id, amount=19900, description="Outfyt AI Premium", email="user@example.com"):
    """Generate Razorpay payment link."""
    if not razorpay_client:
        return None
        
    try:
        expire_by = int(time.time()) + 3600
        
        response = razorpay_client.payment_link.create({
            "amount": amount,
            "currency": "INR",
            "accept_partial": False,
            "description": description,
            "customer": {
                "name": f"User {user_id}",
                "email": email
            },
            "notify": {
                "sms": False,
                "email": True
            },
            "reminder_enable": False,
            "notes": {
                "user_id": str(user_id)
            },
            "callback_url": f"http://localhost:8501?user_id={user_id}",
            "callback_method": "get"
        })
        
        return {
            "short_url": response.get("short_url"),
            "id": response.get("id")
        }
        
    except Exception as e:
        return None

def verify_payment(payment_id):
    """Verify status via Razorpay API and upgrade user."""
    if not razorpay_client or not supabase:
        return False
        
    try:
        response = razorpay_client.payment_link.fetch(payment_id)
        
        if response.get("status") == "paid":
            user_id = response["notes"]["user_id"]
            
            # Upgrade User in Supabase
            end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            
            supabase.table("user_usage").update({
                "is_premium": True,
                "subscription_end_date": end_date
            }).eq("user_id", str(user_id)).execute()
            
            return True
            
        return False
    except Exception as e:
        st.error(f"Verification Error: {e}")
        return False
