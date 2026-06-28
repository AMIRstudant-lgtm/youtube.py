import telebot
from telebot import types
import yt_dlp
import os

# ضع توكن البوت الخاص بك هنا
API_TOKEN="8901446746:AAHa5fKeJBLMCAsGS2VCAJuamXM9kMRvTaQ"
bot = telebot.TeleBot(API_TOKEN)
os.makedirs('downloads', exist_ok=True)

# قاموس النصوص لدعم اللغات الثلاث (العربية، الإنجليزية، الأمهرية)
STRINGS = {
    'ar': {
        'invalid': '❌ أمر غير صالح.',
        'welcome': '👋 أهلاً بك في بوت تحميل فيديوهات يوتيوب! الرجاء اختيار اللغة:',
        'preparing_video': '⏳ جاري تجهيز الفيديو للتحميل، يرجى الانتظار...',
        'download_success': '✅ تم تحميل الفيديو بنجاح!',
        'download_audio_success': '✅ تم تحميل الصوت بنجاح!',
        'video_info': '📊 *معلومات الفيديو:*\n\n👁‍🗨 المشاهدات: {views}\n👤 المشتركون: {subscribers}',
        'choose_format': '🎬 اختر صيغة التحميل المطلوبة:'
    },
    'en': {
        'invalid': '❌ Invalid command.',
        'welcome': '👋 Welcome to YouTube Downloader Bot! Please choose your language:',
        'preparing_video': '⏳ Preparing video for download, please wait...',
        'download_success': '✅ Video downloaded successfully!',
        'download_audio_success': '✅ Audio downloaded successfully!',
        'video_info': '📊 *Video Info:*\n\n👁‍🗨 Views: {views}\n👤 Subscribers: {subscribers}',
        'choose_format': '🎬 Choose the download format:'
    },
    'am': {
        'invalid': '❌ ልክ ያልሆነ ትዕዛዝ።',
        'welcome': '👋 ወደ ዩቲዩብ ቪዲዮ ማውረጃ ቦት በደህና መጡ! እባክዎ ቋንቋዎን ይምረጡ:',
        'preparing_video': '⏳ ቪዲዮው ለማውረድ በመዘጋጀት ላይ ነው፣ እባክዎ ይጠብቁ...',
        'download_success': '✅ ቪዲዮው በተሳካ ሁኔታ ወርዷል!',
        'download_audio_success': '✅ ድምፁ በተሳካ ሁኔታ ወርዷል!',
        'video_info': '📊 *የቪዲዮ መረጃ:*\n\n👁‍🗨 ዕይታዎች: {views}\n👤 ተከታዮች: {subscribers}',
        'choose_format': '🎬 እባክዎ የማውረጃ ቅርጸት ይምረጡ:'
    }
}

# تخزين لغة المستخدم بشكل مؤقت
user_lang = {}
# تخزين رابط الفيديو لكل مستخدم لتسهيل عملية التحميل لاحقاً
user_links = {}

# 1. استقبال الرسائل وبدء اختيار اللغة والرابط
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn_ar = types.InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")
    btn_en = types.InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")
    btn_am = types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="lang_am")
    markup.add(btn_ar, btn_en, btn_am)
    
    bot.reply_to(message, STRINGS['en']['welcome'], reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_video_link(message):
    chat_id = message.chat.id
    if chat_id not in user_lang:
        user_lang[chat_id] = 'ar' # اللغة الافتراضية إذا لم يختار
    
    lang = user_lang[chat_id]
    url = message.text
    
    if "youtube.com" in url or "youtu.be" in url:
        user_links[chat_id] = url
        
        # إنشاء أزرار منفصلة لتحميل الفيديو أو الصوت
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_video = types.InlineKeyboardButton("🎬 Video / فيديو", callback_data="download_video")
        btn_audio = types.InlineKeyboardButton("🎵 Audio / صوت", callback_data="download_audio")
        markup.add(btn_video, btn_audio)
        
        bot.reply_to(message, STRINGS[lang]['choose_format'], reply_markup=markup)
    else:
        bot.reply_to(message, STRINGS[lang]['invalid'])

# 2. معالجة الضغط على الأزرار (Callback Query)
@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    chat_id = call.message.chat.id
    
    # أولاً: إذا كان الضغط لتحديد اللغة
    if call.data.startswith("lang_"):
        lang_code = call.data.split("_")[1]
        user_lang[chat_id] = lang_code
        bot.answer_callback_query(call.id)
        bot.edit_message_text(STRINGS[lang_code]['welcome'], chat_id, call.message.message_id)
        return

    # ثانياً: إذا كان الضغط لخيارات التحميل (فيديو أو صوت) مع جلب الإحصائيات
    lang = user_lang.get(chat_id, 'ar')
    url = user_links.get(chat_id)
    
    if not url:
        bot.answer_callback_query(call.id, text="Error: Link not found!")
        return

    if call.data == "download_video" or call.data == "download_audio":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, STRINGS[lang]['preparing_video'])
        
        # إعدادات yt_dlp لجلب البيانات والتحميل
        if call.data == "download_video":
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
            }
        else:
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
            }
            
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # استخراج معلومات الفيديو بما فيها المشاهدات والمشتركين
                info = ydl.extract_info(url, download=True)
                video_file = ydl.prepare_filename(info)
                
                views = info.get('view_count', 'N/A')
                subscribers = info.get('channel_follower_count', 'N/A') # جلب عدد المشتركين للقناة
                
                # إرسال الإحصائيات للمستخدم أولاً
                stats_text = STRINGS[lang]['video_info'].format(views=views, subscribers=subscribers)
                bot.send_message(chat_id, stats_text, parse_mode="Markdown")
                
                # إرسال الملف (فيديو أو صوت منفصلين) بناءً على ضغطة الزر
                with open(video_file, 'rb') as file:
                    if call.data == "download_video":
                        bot.send_video(chat_id, file, caption=STRINGS[lang]['download_success'])
                    else:
                        bot.send_audio(chat_id, file, caption=STRINGS[lang]['download_audio_success'])
                
                # تنظيف وحذف الملف المحمل محلياً بعد إرساله لتوفير المساحة
                if os.path.exists(video_file):
                    os.remove(video_file)
                    
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {str(e)}")

# تشغيل البوت بشكل مستمر
bot.infinity_polling()
