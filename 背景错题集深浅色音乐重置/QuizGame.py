mWin=0
tno=0
tname=0 
note=0
# tqus=0
blogin=0 
L_info=0 
bnext=0 
v=0

Lresult=0
# tans=0 
ba=0
bb=0
bc=0
bd=0

# 主题和背景相关变量
current_theme = "light"
bg_image = None
correct_sound = None
wrong_sound = None
# 添加全局变量用于存储Frame引用
frml = None
frm2 = None
frm3 = None
frm4 = None
frm5 = None  # 错题回顾页面
bg_canvas = None

# 错题记录相关变量
wrong_questions = {
    "select": [],  # 选择题错题
    "blank": [],   # 填空题错题
    "judge": []    # 判断题错题
}

# 背景音乐相关变量
bg_music = None
music_playing = False
music_volume = 0.5  # 默认音量50%

from Exam import *
qusAndAns=QusAndAns()
qus=qusAndAns.getQusOfSelect()
ans=qusAndAns.getAnsOfSelect()
blanks=qusAndAns.getQusOfBlank()
blank_ans=qusAndAns.getAnsOfBlank()
analyze=qusAndAns.getAnalyzeOfSelect()

pd=qusAndAns.getQusOpd()
pd_ans=qusAndAns.getAnsOpd()
randpd=qusAndAns.getRandQusOfpd()


eName,eTime=qusAndAns.getEnameAndEtime()
randselect=qusAndAns.getRandQusOfSelect()
totalSelect,iselectScore=qusAndAns.getTotalAndiScore()
totalScore=0 
logstate=0 
indexofselect=1
indexofpd=1
# 登录调用函数，验证学号和姓名后初始化游戏
def loginCall():
    global logstate
    sno=tno.get()
    sname=tname.get()
    stu=Stu()
    stu_info=stu.getStu()
    if(sno,sname)in stu_info:
        logstate=1
        mb.showinfo("QuizGame","登录成功，游戏启动！")
        note.tab(1,state="normal")
        tqus.config(state="normal")
        tqus.focus_set()
        tno.config(state="disable")
        tname.config(state="disable")
        blogin['state']="disable"
        tabl = note. tabs()[1]
        note.select(tabl)
        Tl=myTimer(mWin,L_info,eTime*60)
        Tl.start()
    else:
        mb.showinfo("QuizGame","学号或姓名错误！")

def click(event):
    global logstate
    if logstate==0:
        mb.showinfo("QuizGame","请先登录后开始测验游戏！")

def load(event):
    global indexofselect
    tqus.insert("0.0", str(indexofselect)+qus[randselect[0]])
    tqus.config(state="disable")

def radioCall():
    global indexofselect,totalScore
    if(v.get()!=ans[randselect[indexofselect-1]]):
        Lresult['fg']="red"
        Lresult.config(text='错误',font=("宋体",30,"bold"))
        tans.config(state='normal')
        s="答案："+ans[randselect[indexofselect-1]]+"\n"+"解析："+analyze[randselect[indexofselect-1]]
        tans.insert("0.0",s)
        tans.config(state="disable")
        play_wrong_sound()
        # 记录错题
        wrong_questions["select"].append({
            "question": qus[randselect[indexofselect-1]],
            "answer": ans[randselect[indexofselect-1]],
            "analysis": analyze[randselect[indexofselect-1]],
            "user_answer": v.get()
        })
    else:
        Lresult['fg']="green"
        Lresult.config(text="正确",font=("宋体",30,"bold"))
        totalScore+=iselectScore
        play_correct_sound()
    ba.config(state="disable")
    bb.config(state="disable")
    bc.config(state="disable")
    bd.config(state="disable")


def nextCall():
    global indexofselect,T1
    global v
    v.set("E")
    indexofselect+=1
    Lresult.config(text="")
    if(indexofselect>len(qus)):
        indexofselect=len(qus) 
        bnext.config(state="disable")
        mb.showinfo("QuizGame","选择题结束，进入填空题！")
        note.tab(2,state="normal")
        tab2 = note.tabs()[2]
        note.select(tab2)
        load_blank_question()
    ba.config(state="normal")
    bb.config(state="normal")
    bc.config(state="normal")
    bd.config(state="normal")
    tqus.config(state="normal")
    tans.config(state="normal")
    tqus.delete("0.0", "40.200")
    tans.delete("0.0", "40.200")
    tqus.insert('0.0',str(indexofselect)+qus[randselect[indexofselect-1]])
    tqus.config(state="disable")
    tans.config(state="disable")

def nextCallpd():
    global indexofpd, totalScore, vv, tqus1, pd, pd_ans, Lresult1, tans1, bnext1
    vv.set("E")
    indexofpd += 1
    Lresult1.config(text="")
    if indexofpd > len(pd):
        GameOver()
    else:
        ba1.config(state="normal")
        bb1.config(state="normal")
        tqus1.config(state="normal")
        tans1.config(state="normal")
        tqus1.delete("0.0", "end")
        tans1.delete("0.0", "end")
        tqus1.insert("0.0", str(indexofpd) + ". " + pd[indexofpd - 1])
        tqus1.config(state="disable")
        tans1.config(state="disable")
        # Here you can call the function that should be executed after the judgment questions are over# 显示上一题的选择题目
def prev_question():
    global indexofselect
    if indexofselect > 1:
        indexofselect -= 1
    question = qus[randselect[indexofselect - 1]]
    tqus.config(state="normal")
    tqus.delete("0.0", "end")
    tqus.insert("0.0", str(indexofselect) + ". " + question)
    tqus.config(state="disable")
    Lresult.config(text="")
    ba.config(state="normal")
    bb.config(state="normal")
    bc.config(state="normal")
    bd.config(state="normal")

def prev_pd():
    global indexofpd
    if indexofpd > 1:
        indexofpd -= 1
    question = pd[randpd[indexofpd - 1]]
    tqus1.config(state="normal")
    tqus1.delete("0.0", "end")
    tqus1.insert("0.0", str(indexofpd) + ". " + question)
    tqus1.config(state="disable")
    Lresult1.config(text="")
    ba1.config(state="normal")
    bb1.config(state="normal")
   

        
        
# Define function to load the fill-in-the-blank question
def load_blank_question():
    # Load fill-in-the-blank questions
    global blank_index, blanks, blank_ans
    blank_index = 0
    tqus_blank.config(state="normal")
    tqus_blank.insert("0.0", str(blank_index + 1) + blanks[blank_index])
    tqus_blank.config(state="disable")
def load_pd():
    global pd_index, pd, pd_ans
    pd_index = 0
    tqus1.config(state="normal")
    tqus1.insert("0.0", str(pd_index + 1) + pd[pd_index])
    tqus1.config(state="disable")
    


def submit_blank_answer():
    global blank_index, totalScore, blank_ans, blanks
    user_answer = tanswer.get()
    if user_answer == blank_ans[blank_index]:
        totalScore += 10  # Assuming each fill-in-the-blank question is worth 10 points
        Lresult_blank.config(text="正确", font=("宋体", 30, "bold"))
        play_correct_sound()
    else:
        Lresult_blank.config(text="错误", font=("宋体", 30, "bold"))
        tans_blank.config(state="normal")
        s = "答案：" + blank_ans[blank_index] + "\n"
        tans_blank.insert("0.0", s)
        tans_blank.config(state="disable")
        play_wrong_sound()
        # 记录错题
        wrong_questions["blank"].append({
            "question": blanks[blank_index],
            "answer": blank_ans[blank_index],
            "user_answer": user_answer
        })
    blank_index += 1
    if blank_index >= len(blanks):
        mb.showinfo("QuizGame", "填空题结束，进入判断题！")
        note.tab(3,state="normal")
        tab3 = note.tabs()[3]
        note.select(tab3)
        load_pd()
    else:
        tanswer.delete(0, tk.END)
        tqus_blank.config(state="normal")
        tqus_blank.delete("0.0", "40.200")
        tqus_blank.insert("0.0", str(blank_index + 1) + blanks[blank_index])
        tqus_blank.config(state="disable")

def radioCa():
    global indexofpd,totalScore
    if(vv.get()!=pd_ans[randpd[indexofpd-1]]):
        Lresult1['fg']="red"
        Lresult1.config(text='错误',font=("宋体",30,"bold"))
        tans1.config(state='normal')
        s="答案："+pd_ans[randpd[indexofpd-1]]
        tans1.insert("0.0",s)
        tans1.config(state="disable")
        play_wrong_sound()
        # 记录错题
        wrong_questions["judge"].append({
            "question": pd[randpd[indexofpd-1]],
            "answer": pd_ans[randpd[indexofpd-1]],
            "user_answer": vv.get()
        })
    else:
        Lresult1['fg']="green"
        Lresult1.config(text="正确",font=("宋体",30,"bold"))
        totalScore+=iselectScore
        play_correct_sound()
    ba1.config(state="disable")
    bb1.config(state="disable")
    
    
    
    
def GameOver():
    result=TxtFile.getMaxScore()
    if result==-1 or totalScore>result:
        mb.showinfo(title="QuizGame", message="您的分数为：%d\n恭喜您创造了新的得分记录！\n我们将记录你的成绩1！谢谢！"%totalScore)
        sno=tno.get()
        sname=tname.get()
        TxtFile.setNewRecord(sno,sname,totalScore)
    else:
        mb.showinfo(title="QuizGame", message="您的分数为：%d\n对不起，你没有创造新的得分记录！\n下次再努力哦！谢谢！"%totalScore)
    
    # 显示错题回顾页面
    note.tab(4, state="normal")
    tab4 = note.tabs()[4]
    note.select(tab4)
    show_wrong_questions()

def show_wrong_questions():
    """显示错题回顾"""
    wrong_text.config(state="normal")
    wrong_text.delete("0.0", "end")
    
    # 显示选择题错题
    if wrong_questions["select"]:
        wrong_text.insert("end", "选择题错题：\n", "title")
        for i, q in enumerate(wrong_questions["select"], 1):
            wrong_text.insert("end", f"\n{i}. {q['question']}\n")
            wrong_text.insert("end", f"你的答案：{q['user_answer']}\n")
            wrong_text.insert("end", f"正确答案：{q['answer']}\n")
            wrong_text.insert("end", f"解析：{q['analysis']}\n")
            wrong_text.insert("end", "-" * 50 + "\n")
    
    # 显示填空题错题
    if wrong_questions["blank"]:
        wrong_text.insert("end", "\n填空题错题：\n", "title")
        for i, q in enumerate(wrong_questions["blank"], 1):
            wrong_text.insert("end", f"\n{i}. {q['question']}\n")
            wrong_text.insert("end", f"你的答案：{q['user_answer']}\n")
            wrong_text.insert("end", f"正确答案：{q['answer']}\n")
            wrong_text.insert("end", "-" * 50 + "\n")
    
    # 显示判断题错题
    if wrong_questions["judge"]:
        wrong_text.insert("end", "\n判断题错题：\n", "title")
        for i, q in enumerate(wrong_questions["judge"], 1):
            wrong_text.insert("end", f"\n{i}. {q['question']}\n")
            wrong_text.insert("end", f"你的答案：{q['user_answer']}\n")
            wrong_text.insert("end", f"正确答案：{q['answer']}\n")
            wrong_text.insert("end", "-" * 50 + "\n")
    
    wrong_text.tag_configure("title", font=("宋体", 12, "bold"))
    wrong_text.config(state="disabled")

# 导入Tkinter模块，用于创建图形用户界面
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as mb
import tkinter.scrolledtext as sc
import sys
import datetime
import time
from Exam import *
import tkinter.filedialog as fd
from PIL import Image, ImageTk
import pygame
import math

# 初始化pygame音频
pygame.mixer.init()

def load_sounds():
    global correct_sound, wrong_sound
    try:
        # 尝试加载音效文件
        correct_sound = pygame.mixer.Sound("sounds/correct.wav")
        wrong_sound = pygame.mixer.Sound("sounds/wrong.wav")
    except:
        print("音效文件未找到，将使用默认音效")
        # 创建更好的默认音效
        # 正确音效：欢快的上升音阶
        correct_buffer = bytes([max(0, min(255, int(127 * (1 + math.sin(i/5) + 0.5 * math.sin(i/2.5))))) for i in range(2000)])
        # 错误音效：低沉的下降音阶
        wrong_buffer = bytes([max(0, min(255, int(127 * (1 - math.sin(i/8) - 0.3 * math.sin(i/4))))) for i in range(2000)])
        correct_sound = pygame.mixer.Sound(buffer=correct_buffer)
        wrong_sound = pygame.mixer.Sound(buffer=wrong_buffer)
        # 设置音量
        correct_sound.set_volume(0.5)
        wrong_sound.set_volume(0.5)

def play_correct_sound():
    try:
        if correct_sound:
            correct_sound.play()
    except Exception as e:
        print(f"播放正确音效时出错: {e}")

def play_wrong_sound():
    try:
        if wrong_sound:
            wrong_sound.play()
    except Exception as e:
        print(f"播放错误音效时出错: {e}")

def toggle_theme():
    global current_theme, bg_canvas
    if current_theme == "light":
        current_theme = "dark"
        style.configure("TFrame", background="#2b2b2b")
        style.configure("TLabel", background="#2b2b2b", foreground="white")
        style.configure("TButton", background="#3b3b3b", foreground="white")
        style.configure("TRadiobutton", background="#2b2b2b", foreground="white")
        style.configure("TNotebook", background="#2b2b2b")
        style.configure("TNotebook.Tab", background="#3b3b3b", foreground="white")
        if bg_canvas:
            bg_canvas.configure(bg="#2b2b2b")
    else:
        current_theme = "light"
        style.configure("TFrame", background="white")
        style.configure("TLabel", background="white", foreground="black")
        style.configure("TButton", background="#f0f0f0", foreground="black")
        style.configure("TRadiobutton", background="white", foreground="black")
        style.configure("TNotebook", background="white")
        style.configure("TNotebook.Tab", background="#f0f0f0", foreground="black")
        if bg_canvas:
            bg_canvas.configure(bg="white")

def import_background():
    global bg_image, bg_canvas
    file_path = fd.askopenfilename(
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
    )
    if file_path:
        try:
            # 加载并调整图片大小以适应窗口
            image = Image.open(file_path)
            image = image.resize((800, 600), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(image)
            
            # 如果Canvas已存在，更新图片
            if bg_canvas:
                bg_canvas.delete("all")
                bg_canvas.create_image(0, 0, image=bg_image, anchor="nw", tags="background")
            else:
                # 创建新的Canvas
                bg_canvas = tk.Canvas(mWin, width=800, height=600, highlightthickness=0)
                bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
                bg_canvas.create_image(0, 0, image=bg_image, anchor="nw", tags="background")
                
                # 将Canvas置于底层
                bg_canvas.tag_lower("background")
                
                # 调整其他控件的层级
                theme_frame.lift()
                note.lift()
                L_info.lift()
                
        except Exception as e:
            mb.showerror("错误", f"无法加载背景图片: {str(e)}")

# 定义一个计时器类，用于在GUI中显示倒计时
class myTimer:
    # 初始化计时器对象，设置窗口、标签、持续时间、超时时调用的函数
    def __init__(self,window,label,seconds):
        self.hours=0
        self.minutes=0
        self.seconds=0
        self.is_running=False # 计时器是否正在运行的标志
        self.start_time=None
        self.window=window
        self.label=label
        self.duration=seconds
    # 将秒数格式化为分钟和秒的格式    
    def format_time(self,seconds):
        self.hours=seconds//3600
        self.minutes=(seconds%3600)//60
        self.seconds=seconds%60
        return "%02d:%02d:%02d"%(self.hours, self.minutes, self.seconds)
    # 更新时间显示的函数
    def update_time(self):
        if self.is_running:
            remaining_time = self.duration - (datetime.datetime.now()-self.start_time).total_seconds()
        if remaining_time<=0:
            self.is_running = False
            self.label.config(text="剩余时间："+self.format_time(0))
            GameOver()
        else:
            t=self.format_time(int(remaining_time))
            self.label.config(text="学号：%s   姓名：%s   剩余时间：%s"%(tno.get(),tname.get(),t))
            self.window.after(1000, self.update_time)
      # 开始计时器       
    def start(self):
        self.start_time = datetime.datetime.now()
        self.is_running = True
        self.update_time()
# 停止计时器
    def stop(self):
        self.is_running = False
        self.format_time(0)

def load_background_music():
    global bg_music, music_playing
    file_path = fd.askopenfilename(
        filetypes=[("Audio files", "*.mp3 *.wav")]
    )
    if file_path:
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(music_volume)
            bg_music = file_path  # 保存音乐文件路径
            pygame.mixer.music.play(-1)  # 立即开始播放并循环
            music_playing = True
            mb.showinfo("成功", "背景音乐加载成功并开始播放！")
        except Exception as e:
            mb.showerror("错误", f"无法加载背景音乐: {str(e)}")

def toggle_music():
    global music_playing
    if not bg_music:
        mb.showinfo("提示", "请先导入背景音乐！")
        return
    
    if music_playing:
        pygame.mixer.music.pause()
        music_playing = False
    else:
        pygame.mixer.music.unpause()  # 使用unpause而不是play
        music_playing = True

def adjust_volume(value):
    global music_volume
    music_volume = float(value)
    pygame.mixer.music.set_volume(music_volume)
    if correct_sound:
        correct_sound.set_volume(music_volume)
    if wrong_sound:
        wrong_sound.set_volume(music_volume)

def main():
# 使用 global 关键字声明，使得以下变量在函数内部可修改，它们在函数外也被定义
    global mWin,tno,tname,note,tqus,blogin,L_info,bnext,bprev,v,vv,Lresult,tans,ba,bb,bc,bd,blank_index, tqus_blank, tanswer, bsubmit_blank, Lresult_blank, tans_blank, blanks, blank_ans,bnext1,bprev1,Lans1,tans1,tqus1,Lresult1,Lqus1,Lans1,ba1,bb1,pd_index,tqus_pd, pd, pd_ans, style, frml, frm2, frm3, frm4, frm5, bg_canvas, theme_frame, wrong_text
# 创建一个 Tkinter 主窗口实例，并赋值给全局变量 mWin
    mWin=tk.Tk()
# 获取屏幕的宽度和高度，用于计算窗口的起始位置
    x=mWin.winfo_screenwidth()
    y=mWin.winfo_screenheight()
 # 计算窗口的 x 和 y 起始坐标，使得窗口在屏幕中居中
    x=(x-800)//2
    y=(y-600)//2
# 设置窗口的尺寸和位置
    mWin.geometry(f"800x600+{x}+{y}")
# 禁止用户调整窗口大小
    mWin.resizable(width=False, height=False)
# 设置窗口标题，显示游戏名称、测验名称和持续时间
    mWin.title("欢迎使用QuizGame"+""*50+"测验名称："+eName+""*10+"测验时长（分）:"+str(eTime))

    # 初始化音效
    load_sounds()

    # 创建主题切换和背景导入按钮的容器
    style = ttk.Style()
    theme_frame = ttk.Frame(mWin)
    theme_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
    
    # 创建主题切换和背景导入按钮
    theme_btn = ttk.Button(theme_frame, text="切换主题", command=toggle_theme, width=10)
    theme_btn.pack(side=tk.LEFT, padx=5)
    
    bg_btn = ttk.Button(theme_frame, text="导入背景", command=import_background, width=10)
    bg_btn.pack(side=tk.LEFT, padx=5)

    # 添加音乐控制相关控件
    music_btn = ttk.Button(theme_frame, text="导入音乐", command=load_background_music, width=10)
    music_btn.pack(side=tk.LEFT, padx=5)

    play_pause_btn = ttk.Button(theme_frame, text="播放/暂停", command=toggle_music, width=10)
    play_pause_btn.pack(side=tk.LEFT, padx=5)

    volume_label = ttk.Label(theme_frame, text="音量:")
    volume_label.pack(side=tk.LEFT, padx=5)

    volume_scale = ttk.Scale(theme_frame, from_=0, to=1, orient=tk.HORIZONTAL, 
                            length=100, command=adjust_volume)
    volume_scale.set(music_volume)
    volume_scale.pack(side=tk.LEFT, padx=5)

# 创建一个 Label 控件用于显示剩余时间，并放置在窗口底部
    L_info=ttk.Label(mWin, text="剩余时间：")
    L_info.pack(side=tk.BOTTOM)
# 创建一个 Notebook 控件，用于在不同页面间进行切换，并填充整个窗口
    note=ttk.Notebook(mWin)
    note.pack(fill="both",expand=True)
# 创建登录页面的 Frame 容器，并添加到 Notebook 控件中
    frml=ttk.Frame(note)
    frml.pack(fill="both",expand=True)
    note.add(frml,text="登录")
# 在登录页面中创建一个 ScrolledText 控件，用于显示游戏说明
    textl=sc.ScrolledText (frml,height=30,width=100,wrap=tk.WORD)
# 在 ScrolledText 控件中插入游戏说明的标题和内容
    textl.insert("0.0","\n\n"+"QuizGame游戏说明".center(100))
    textl.insert("25.0 linestart", "\n\n\n\n"+TxtFile.getGameInfo())
# 创建学号和姓名的 Label 和 Entry 控件，以及登录按钮，并设置它们在页面中的布局
    lno=ttk.Label (frml, text="学号：")
    lname=ttk.Label (frml, text="姓名：")
    tno=ttk.Entry(frml)
    tname=ttk.Entry(frml)
    blogin=ttk.Button(frml,text="登录",command=loginCall)

# 使用 grid 布局管理器对登录页面的控件进行布局
    textl.grid(column=0, row=0, columnspan=8, rowspan=30, padx=50,pady=20,sticky=tk.E)
    lno.grid(column=3,row=30,padx=2,pady=5,sticky=tk.E)
    tno.grid(column=4,row=30,padx=2,pady=5,sticky=tk.W) 
    lname.grid(column=3,row=31,padx=2, pady=5, sticky=tk.E)
    tname.grid(column=4,row=31,padx=2,pady=5, sticky=tk. W)
    blogin.grid(column=4,row=32,padx=5,pady=5,sticky=tk.W)
# 创建选择题页面的 Frame 容器，并添加到 Notebook 控件中
    frm2=ttk.Frame(note)
    frm2.pack(fill="both",expand=True)
    note.add(frm2, text="选择题",state="disabled")
 # 在选择题页面中创建 Label 和 ScrolledText 控件用于显示题目，以及 Radiobutton 控件用于选择答案
    Lqus=ttk.Label(frm2,text="题目：")
    tqus=sc.ScrolledText(frm2)
    tqus.config(state="disabled")
    v=tk.StringVar()# 创建一个字符串变量，用于跟踪 Radiobutton 的选择
    ba=ttk.Radiobutton(frm2, text="A", variable=v, value="A",command=radioCall)
    bb=ttk.Radiobutton(frm2, text="B", variable=v, value="B",command=radioCall)
    bc=ttk.Radiobutton(frm2, text="C", variable=v, value="C",command=radioCall)
    bd=ttk.Radiobutton(frm2, text="D", variable=v, value="D",command=radioCall)
# 创建下一题和上一题的按钮，以及解析 Label 和 ScrolledText 控件
    bnext=ttk.Button(frm2,text="下一题",command=nextCall)
    bprev = ttk.Button(frm2, text="上一题", command=prev_question)
    Lans=ttk.Label(frm2,text="解析：")
    tans=sc.ScrolledText(frm2) 
    tans.config(state="disabled")
# 为题目文本框添加当获得焦点时自动加载题目的事件绑定
    tqus.bind("<FocusIn>",load)
# 创建用于显示用户答题结果的 Label 控件
    Lresult=tk.Label(frm2)
 # 使用 grid 布局管理器对选择题页面的控件进行布局
    Lqus.grid(column=0, row=1, padx=20,pady=15, sticky=tk.W)
    Lans.grid(column=9, row=1, padx=5, pady=15,sticky=tk.W)
    tqus.config(height=30,width=80)
    tqus.grid(column=0, row=2, columnspan=9, rowspan=30,padx=20,pady=5, sticky=tk.E)
    tans.config(height=30,width=20)
    tans.grid(column=9,row=2,columnspan=3, rowspan=30, padx=5,pady=5,sticky=tk.E)
    ba.grid(column=2,row=33,padx=2,pady=5,sticky=tk.E)
    bb.grid(column=3,row=33,padx=2,pady=5,sticky=tk.E)
    bc.grid(column=4,row=33,padx=2,pady=5,sticky=tk.E)
    bd.grid(column=5,row=33,padx=2,pady=5,sticky=tk.E)
    bprev.grid(column=2, row=36, columnspan=2, padx=2, pady=5,sticky=tk.E)
    bnext.grid(column=4, row=36, columnspan=2, padx=2, pady=5,sticky=tk.E)
    Lresult.grid(column=9,row=36,padx=2,pady=5)
# 创建填空题页面的 Frame 容器，并添加到 Notebook 控件中
    frm3=ttk.Frame(note)
    frm3.pack(fill='both',expand=True)
    note.add(frm3,text="填空题",state="disabled")
# 在填空题页面中创建 Label 和 ScrolledText 控件用于显示题目，以及 Entry 控件用于输入答案
    Lqus_blank = ttk.Label(frm3, text="题目：")
    tqus_blank = sc.ScrolledText(frm3)
    tqus_blank.config(state="disabled")
    Lanswer = ttk.Label(frm3, text="您的答案：")
    tanswer = ttk.Entry(frm3)

# 创建提交答案的按钮
    bsubmit_blank = ttk.Button(frm3, text="下一题", command=submit_blank_answer)


# 创建用于显示用户答题结果的 Label 控件
    Lresult_blank = ttk.Label(frm3)
    Lans_blank = ttk.Label(frm3, text="解析：")
    tans_blank = sc.ScrolledText(frm3)
    tans_blank.config(state="disabled")
# 使用 grid 布局管理器对填空题页面的控件进行布局
    Lqus_blank.grid(column=0, row=1, padx=20, pady=15, sticky=tk.W)
    Lanswer.grid(column=0, row=33, padx=2, pady=5, sticky=tk.E)
    tanswer.grid(column=1, row=33, padx=2, pady=5, sticky=tk.W)
    bsubmit_blank.grid(column=2, row=33, padx=2, pady=5, sticky=tk.W)
    Lans_blank.grid(column=9, row=1, padx=5, pady=15, sticky=tk.W)
    tqus_blank.config(height=30, width=80)
    tqus_blank.grid(column=0, row=2, columnspan=9, rowspan=30, padx=20, pady=5, sticky=tk.E)
    tans_blank.config(height=30, width=20)
    tans_blank.grid(column=9, row=2, columnspan=3, rowspan=30, padx=5, pady=5, sticky=tk.E)
    Lresult_blank.grid(column=9, row=36, padx=2, pady=5)



# 创建判断题页面的 Frame 容器，并添加到 Notebook 控件中
    frm4=ttk.Frame(note)
    frm4.pack(fill='both',expand=True)
    note.add(frm4,text="判断题",state="disabled")
 # 在判断题页面中创建 Label 和 ScrolledText 控件用于显示题目，以及 Radiobutton 控件用于选择答案
    Lqus1=ttk.Label(frm4,text="题目：")
    tqus1=sc.ScrolledText(frm4)
    tqus1.config(state="disabled")
    vv=tk.StringVar()# 创建一个字符串变量，用于跟踪 Radiobutton 的选择
    ba1=ttk.Radiobutton(frm4, text="A", variable=vv, value="A",command=radioCa)
    bb1=ttk.Radiobutton(frm4, text="B", variable=vv, value="B",command=radioCa)


# 创建下一题和上一题的按钮，以及解析 Label 和 ScrolledText 控件
    bnext1=ttk.Button(frm4,text="下一题",command=nextCallpd)
    bprev1 = ttk.Button(frm4, text="上一题", command=prev_pd)
    Lans1=ttk.Label(frm4,text="解析：")
    tans1=sc.ScrolledText(frm4) 
    tans1.config(state="disabled")
# 为题目文本框添加当获得焦点时自动加载题目的事件绑定
    tqus1.bind("<FocusIn>",load)
# 创建用于显示用户答题结果的 Label 控件
    Lresult1=tk.Label(frm4)
 # 使用 grid 布局管理器对选择题页面的控件进行布局
    Lqus1.grid(column=0, row=1, padx=20,pady=15, sticky=tk.W)
    Lans1.grid(column=9, row=1, padx=5, pady=15,sticky=tk.W)
    tqus1.config(height=30,width=80)
    tqus1.grid(column=0, row=2, columnspan=9, rowspan=30,padx=20,pady=5, sticky=tk.E)
    tans1.config(height=30,width=20)
    tans1.grid(column=9,row=2,columnspan=3, rowspan=30, padx=5,pady=5,sticky=tk.E)
    ba1.grid(column=2,row=33,padx=2,pady=5,sticky=tk.E)
    bb1.grid(column=3,row=33,padx=2,pady=5,sticky=tk.E)
    bprev1.grid(column=2, row=36, columnspan=2, padx=2, pady=5,sticky=tk.E)
    bnext1.grid(column=4, row=36, columnspan=2, padx=2, pady=5,sticky=tk.E)
    Lresult1.grid(column=9,row=36,padx=2,pady=5)

 # 为整个 Notebook 控件添加点击事件，用于处理点击行为
    note.bind("<Button-1>",click)

    # 创建错题回顾页面
    frm5 = ttk.Frame(note)
    frm5.pack(fill='both', expand=True)
    note.add(frm5, text="错题回顾", state="disabled")
    
    # 创建错题显示区域
    wrong_text = sc.ScrolledText(frm5, wrap=tk.WORD)
    wrong_text.pack(fill='both', expand=True, padx=10, pady=10)
    wrong_text.config(state="disabled")

    mWin.mainloop()
    
if __name__=="__main__":
    main()
