import time
import pytz
import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from selenium import webdriver
from selenium.webdriver.common.by import By

##########################################################################################

# 設定時區為 UTC+8 中原標準時間
cst_timezone = pytz.timezone('Asia/Taipei')

# 當前執行的 Thread ID
current_thread_id = None

##########################################################################################

# 建立主視窗
root = tk.Tk()
root.title("搶琴房大作戰")

# 設定全局字體大小
global_font_size = 16
root.option_add("*Font", f"TkDefaultFont {global_font_size}")

# 創建帳號輸入欄位
account_label = tk.Label(root, text="帳號(Account):")
account_label.pack(pady=(15, 0.5))
account_entry = tk.Entry(root)
account_entry.pack(pady=2)

# 創建密碼輸入欄位
password_label = tk.Label(root, text="密碼(Password):")
password_label.pack(pady=(14, 0.5))
password_entry = tk.Entry(root, show="*")
password_entry.pack(pady=2)

# 創建開搶時間輸入欄位，使用 Combobox 來選擇時間
time_label = tk.Label(root, text="開搶時間(Start Time):")
time_label.pack(pady=(16, 0.5))
time_frame = tk.Frame(root)
time_frame.pack(pady=2)

hours = [str(i).zfill(2) for i in range(24)]  # 00 到 23 小時
minutes = [str(i).zfill(2) for i in range(60)]  # 00 到 59 分鐘
seconds = [str(i).zfill(2) for i in range(60)]  # 00 到 59 秒

# 自訂 Combobox 樣式，並調整寬度
style = ttk.Style()
style.configure('Custom.TCombobox', padding=5, width=3)  # 調整寬度為 3

hour_combo = ttk.Combobox(time_frame, values=hours,
                          style='Custom.TCombobox', width=5)
minute_combo = ttk.Combobox(
    time_frame, values=minutes, style='Custom.TCombobox', width=5)
second_combo = ttk.Combobox(
    time_frame, values=seconds, style='Custom.TCombobox', width=5)

hour_combo.grid(row=0, column=0)
tk.Label(time_frame, text=":").grid(row=0, column=1)
minute_combo.grid(row=0, column=2)
tk.Label(time_frame, text=":").grid(row=0, column=3)
second_combo.grid(row=0, column=4)

# 創建目標練琴時段輸入欄位
slots_frame_1 = tk.Frame(root)
slots_frame_1.pack(pady=(17, 1.5))
label = tk.Label(slots_frame_1, text="目標練琴時段(Target Time Slots):")
label.grid(row=0, columnspan=5)

# 創建 Frame 用於放置複選框
slots_frame_2 = tk.Frame(root)
slots_frame_2.pack()

# 創建複選框並放置到 Frame 中
checkbuttons = []
for i in range(7, 22):
    var = tk.IntVar()
    formatted_text = f"{i:02}"  # 將數字格式化為兩位數字串
    checkbutton = tk.Checkbutton(slots_frame_2, text=formatted_text, variable=var)
    checkbutton.grid(row=(i - 7) // 5, column=(i - 7) % 5, padx=5, pady=5)
    checkbuttons.append(var)

# 加入圖片
img = Image.open('./大耳狗.jpeg')

# 設定要縮小到的寬度和高度
new_width = 200
new_height = 200

# 進行縮小
img = img.resize((new_width, new_height), Image.LANCZOS)  # 使用ANTIALIAS濾鏡進行縮小

tk_img = ImageTk.PhotoImage(img)

canvas = tk.Canvas(root, width=new_width, height=new_height)
canvas.pack(pady=(15, 2))

canvas.create_image(0, 0, anchor='nw', image=tk_img)   # 在 Canvas 中放入圖片

##########################################################################################

# 定義一個函數來檢查輸入並執行儲存或顯示錯誤訊息
def check_and_save():
    user_account = account_entry.get()
    user_password = password_entry.get()
    selected_hour = hour_combo.get()
    selected_minute = minute_combo.get()
    selected_second = second_combo.get()

    # 檢查是否有未輸入的欄位
    if not user_account or not user_password or not selected_hour or not selected_minute or not selected_second:
        messagebox.showerror("錯誤", "請填寫完整的帳號、密碼與時間")
        return

    # 檢查開搶時間是否符合規範
    try:
        selected_hour = int(selected_hour)
        selected_minute = int(selected_minute)
        selected_second = int(selected_second)
        if selected_hour < 0 or selected_hour > 23 or selected_minute < 0 or selected_minute > 59 or selected_second < 0 or selected_second > 59:
            messagebox.showerror("錯誤", "請輸入有效的時間")
            return
    except ValueError:
        messagebox.showerror("錯誤", "請輸入有效的時間")
        return

    # 如果通過檢查，則執行儲存
    selected_time = f"{selected_hour}:{selected_minute}:{selected_second}"
    
    # 儲存並檢查目標練琴時段是否符合規範
    target_time_slot_list = []
    for row in range(3):
        for col in range(5):
            index = row * 5 + col
            if checkbuttons[index].get() == 1:
                time = index + 7  # 因為時段是 7 到 21
                target_time_slot_list.append(time)

    print("目標練琴時段:", target_time_slot_list)
    
    # 啟動新執行緒
    t = threading.Thread(target=background_time_check, args=(
        user_account, user_password, selected_hour, selected_minute, selected_second, target_time_slot_list))
    t.daemon = True
    t.start()
    
    # 啟動成功提示訊息
    messagebox.showinfo("提示", f"啟動成功！正在背景等待 {selected_time} 的到來！")
    
    
def background_time_check(user_account, user_password, selected_hour, selected_minute, selected_second, target_time_slot_list):
    # 更新當前 Thread ID
    global current_thread_id
    current_thread_id = threading.get_ident()
    # 準備登入的時間
    current_time_cst = datetime.now(cst_timezone)
    prepare_time = datetime(year=current_time_cst.year, month=current_time_cst.month, day=current_time_cst.day, hour=selected_hour, minute=selected_minute, second=selected_second)
    prepare_time = prepare_time + timedelta(minutes=-1)
    prepare_hour, prepare_minute, prepare_second = prepare_time.hour, prepare_time.minute, prepare_time.second
    while True:
        # 檢查若有新的 Thread 啟動，則停止目前的 Thread
        if current_thread_id != threading.get_ident():
            break
        # 獲取當前時間，並設定時區為中原標準時間
        current_time_cst = datetime.now(cst_timezone)
        current_hour, current_minute, current_second = current_time_cst.hour, current_time_cst.minute, current_time_cst.second
        # 檢查當前時間
        if current_hour == prepare_hour and current_minute == prepare_minute and current_second == prepare_second:
            # 如果當前時間等於使用者輸入的時間，則執行 Selenium 任務
            run_selenium(user_account=user_account, user_password=user_password, selected_hour=selected_hour, selected_minute=selected_minute, selected_second=selected_second, target_time_slot_list=target_time_slot_list)
            # 執行完畢後退出迴圈
            break

        # 等待0.8秒再檢查一次，避免無限迴圈造成系統負擔
        time.sleep(0.8)
    return
    
    
def run_selenium(user_account, user_password, selected_hour, selected_minute, selected_second, target_time_slot_list):
    # 執行驅動
    driver = webdriver.Chrome()
    driver.get('https://iportal.ntnu.edu.tw/ntnu/')
    # time.sleep(1)
    # driver.find_element(By.XPATH, '//*[@id = "loginbutton"]/a').click()
    # time.sleep(1)
    # 輸入帳號
    account = driver.find_element(By.XPATH, '//*[@id="muid"]')
    account.clear()
    account.send_keys(user_account)
    # time.sleep(1)
    # 輸入密碼
    password = driver.find_element(By.XPATH, '//*[@id="mpassword"]')
    password.clear()
    password.send_keys(user_password)
    # time.sleep(1)
    # 執行登入
    driver.find_element(
        By.XPATH, '/html/body/table[2]/tbody/tr[2]/td/table/tbody/tr[2]/td[3]/table/tbody/tr[2]/td/table[1]/tbody/tr[2]/td/div/input').click()
    while True:
        # 獲取當前時間，並設定時區為中原標準時間
        current_time_cst = datetime.now(cst_timezone)
        current_hour, current_minute, current_second = current_time_cst.hour, current_time_cst.minute, current_time_cst.second
        # 檢查目標時間
        if current_hour == selected_hour and current_minute == selected_minute and current_second == selected_second:
            # 預約琴房
            driver.find_element(
                By.XPATH, '//*[@id="divStandaptree"]/ul/li[23]/a').click()
            # 切換視窗
            window_after = driver.window_handles[1]
            driver.switch_to.window(window_after)
            # 進入預約畫面
            driver.find_element(
                By.XPATH, '/html/body/div[2]/div/div/div[2]/div[1]/div[2]/div').click()
            # 選擇預約的目標
            prefix = 0
            for target_time_slot in target_time_slot_list:
                # 定位位置
                idx = target_time_slot - 6 - prefix
                # 點擊預約
                while True:
                    try:
                        driver.find_element(
                            By.XPATH, f'//*[@id="bookme1020Tbl"]/tbody/tr[{idx}]/td[3]/button').click()
                        break
                    except:
                        continue
                # 關閉彈出視窗
                while True:
                    try:
                        driver.find_element(
                            By.XPATH, f'/html/body/div[2]/div[2]/div/div/div/div/div/div/div/div[4]/button').click()
                        break
                    except:
                        continue
                # 因為預約某時段後，該時段選項會消失，因此每預約一間就要減1
                prefix += 1
            time.sleep(30)
            break

        # 等待0.1秒再檢查一次
        time.sleep(0.01)

    # 搶琴房完成提示訊息
    messagebox.showinfo("提示", "搶琴房成功！")
    return
        
   
def main():
    # 創建儲存按鈕
    save_button = tk.Button(root, text="開始", padx=12, pady=8, command=check_and_save)
    save_button.pack(pady=(13, 2))
    # 選擇視窗大小
    window_width = 630
    window_height = 680
    # 使視窗位於螢幕中央
    x = (root.winfo_screenwidth() - window_width) // 2
    y = int((root.winfo_screenheight() - window_height) // 2.8)
    # 固定視窗大小
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    # 禁止視窗的大小調整
    root.resizable(False, False)
    # 啟動主迴圈
    root.mainloop()
    
##########################################################################################

if __name__ == '__main__':
    main()
