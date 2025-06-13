import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from Exam import TxtFile, Stu, QusAndAns
import pygame
import threading
import os
import sys
import numpy
import win32gui
import win32con
import winsound
import time
try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("错误", "请先安装 Pillow 库：\npip install Pillow")
    sys.exit(1)

class QuizGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QuizGame 测验系统")
        self.root.geometry("900x750")
        
        # 初始化音乐播放相关属性
        self.current_music = None
        self.music_playing = False
        self.volume = 0.5  # 默认音量50%
        self.music_thread = None
        self.music_control_frame = None
        self.audio_available = False  # 添加音频可用性标志
        
        # 初始化主题和背景相关属性
        self.is_dark_mode = False
        self.current_bg_image = None
        self.bg_image_path = None
        self.bg_label = None
        self.theme_colors = {
            'light': {
                'bg': '#f0f0f0',
                'text': 'black',
                'button': '#4CAF50',
                'button_text': 'white',
                'frame_bg': '#ffffff',
                'highlight': '#e6f3ff'
            },
            'dark': {
                'bg': '#2b2b2b',
                'text': 'white',
                'button': '#45a049',
                'button_text': 'white',
                'frame_bg': '#3b3b3b',
                'highlight': '#1a1a1a'
            }
        }
        
        # 初始化游戏模式相关属性
        self.game_mode = "simple" # "simple", "medium" or "hard"
        self.question_timer_id = None
        self.question_time_left = None
        self.mode_times = {
            "simple": 20,
            "medium": 10,
            "hard": 5
        }
        
        # 尝试初始化pygame音频
        try:
            pygame.mixer.init()
            self.audio_available = True
        except pygame.error as e:
            print(f"音频初始化失败: {str(e)}")
            self.audio_available = False
            messagebox.showwarning("音频初始化警告", 
                "无法初始化音频系统，音乐播放功能将不可用。\n"
                "请检查您的音频设备是否正确连接和配置。")
        
        # 获取程序所在目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是直接运行的python脚本
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        # 设置音效文件路径
        sounds_dir = os.path.join(application_path, "sounds")
        
        # 确保sounds目录存在
        if not os.path.exists(sounds_dir):
            os.makedirs(sounds_dir)
            
        # 加载音效，如果文件不存在则使用默认音效
        try:
            correct_sound_path = os.path.join(sounds_dir, "correct.wav")
            wrong_sound_path = os.path.join(sounds_dir, "wrong.wav")
            
            if os.path.exists(correct_sound_path):
                self.correct_sound = pygame.mixer.Sound(correct_sound_path)
            else:
                # 创建一个简单的正确音效
                self.correct_sound = self.create_default_correct_sound()
                
            if os.path.exists(wrong_sound_path):
                self.wrong_sound = pygame.mixer.Sound(wrong_sound_path)
            else:
                # 创建一个简单的错误音效
                self.wrong_sound = self.create_default_wrong_sound()
                
        except Exception as e:
            print(f"加载音效时出错: {str(e)}")
            # 创建默认音效
            self.correct_sound = self.create_default_correct_sound()
            self.wrong_sound = self.create_default_wrong_sound()
        
        self.student_id = ""
        self.student_name = ""
        self.current_question = 0
        self.score = 0
        self.time_left = 0
        self.timer_running = False
        self.time_label = None
        self.score_label = None
        self.progress_frame = None
        self.progress_labels = []
        self.questions = []
        self.wrong_questions = []
        self.collected_questions = []  # 收藏的错题（或直接收藏的普通题）
        self.stage = "login"
        self.fav_btn = None
        
        # 添加题型统计
        self.question_stats = {
            'select': {'total': 0, 'correct': 0},
            'fill': {'total': 0, 'correct': 0},
            'tf': {'total': 0, 'correct': 0}
        }
        
        try:
            self.students = Stu().getstu()
            self.quiz = QusAndAns()
            all_questions = self.quiz.getQuestions()
            select_questions = [q for q in all_questions if q['type'] == 'select'][:5]
            fill_questions = [q for q in all_questions if q['type'] == 'fill'][:5]
            tf_questions = [q for q in all_questions if q['type'] == 'tf'][:5]
            self.questions = select_questions + fill_questions + tf_questions
            self.time_left = self.quiz.examTime * 60
        except Exception as e:
            messagebox.showerror("初始化错误", f"初始化失败: {str(e)}")
            self.root.destroy()
            return
        
        self.create_login_ui()

    def get_stages(self):
        # 动态返回当前阶段列表
        base = ["登录", "选择题", "填空题", "判断题"]
        # 始终显示错题回顾
        base.append("错题回顾")
        # 如果有收藏的题目，显示收藏集
        if len(self.collected_questions) > 0:
            base.append("收藏集")
        return base

    def clear(self):
        """清除所有组件，但保留背景图片"""
        for widget in self.root.winfo_children():
            if widget != getattr(self, 'bg_label', None):
                widget.destroy()

    def clear_except_timer(self):
        """清除除计时器和背景图片外的所有组件"""
        for widget in self.root.winfo_children():
            if widget not in [self.time_label, self.score_label, self.progress_frame, getattr(self, 'bg_label', None)]:
                widget.destroy()

    def create_progress_indicator(self):
        if self.progress_frame:
            self.progress_frame.destroy()
            
        # 创建顶部控制栏
        control_frame = tk.Frame(self.root, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # 添加主题切换按钮
        theme_btn = tk.Button(control_frame, 
                            text="🌓 切换主题", 
                            command=self.toggle_theme,
                            font=("Arial", 10),
                            bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                            fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text'])
        theme_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加背景控制按钮
        bg_btn = tk.Button(control_frame, 
                          text="🖼️ 导入背景", 
                          command=self.import_background,
                          font=("Arial", 10),
                          bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                          fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text'])
        bg_btn.pack(side=tk.LEFT, padx=5)
        
        if self.current_bg_image:
            remove_bg_btn = tk.Button(control_frame, 
                                    text="❌ 移除背景", 
                                    command=self.remove_background,
                                    font=("Arial", 10),
                                    bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                                    fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text'])
            remove_bg_btn.pack(side=tk.LEFT, padx=5)
            
        # 创建进度指示器框架
        self.progress_frame = tk.Frame(self.root, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        self.progress_frame.pack(side=tk.TOP, anchor="ne", padx=10, pady=10)
        stages = self.get_stages()
        self.progress_labels = []
        for i, stage in enumerate(stages):
            highlight = False
            if self.stage == "login" and stage == "登录":
                highlight = True
            elif self.stage == "select" and stage == "选择题":
                highlight = True
            elif self.stage == "fill" and stage == "填空题":
                highlight = True
            elif self.stage == "tf" and stage == "判断题":
                highlight = True
            elif self.stage == "collected" and stage == "收藏集":
                highlight = True
            elif self.stage == "review" and stage == "错题回顾":
                highlight = True
            fg = "red" if highlight else "gray"
            font = ("Arial", 10, "bold") if highlight else ("Arial", 10)
            label = tk.Label(self.progress_frame, text=stage, fg=fg, font=font, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
            label.grid(row=0, column=i, padx=5)
            self.progress_labels.append(label)

    def create_score_indicator(self):
        if hasattr(self, 'score_label') and self.score_label is not None:
            self.score_label.destroy()
        self.score_label = tk.Label(self.root, text=f"当前得分: {self.score}", 
                                  font=("Arial", 12, "bold"), fg="blue", bg="#e6f3ff")
        self.score_label.pack(side=tk.TOP, anchor="ne", padx=10, pady=5)
        # 收藏集按钮，仅有收藏时出现且避免重复
        if len(self.collected_questions) > 0 and self.stage not in ["login", "end", "collected"]:
            if not hasattr(self, "fav_btn") or self.fav_btn is None or not self.fav_btn.winfo_exists():
                self.fav_btn = tk.Button(self.root, text="收藏集", command=self.show_collected, font=("Arial", 10), bg="#FF9800", fg="white")
                self.fav_btn.pack(side=tk.TOP, anchor="ne", padx=10, pady=10)
        else:
            if hasattr(self, "fav_btn") and self.fav_btn is not None and self.fav_btn.winfo_exists():
                self.fav_btn.destroy()
                self.fav_btn = None

    def create_music_controls(self):
        """创建音乐控制面板"""
        if self.music_control_frame:
            self.music_control_frame.destroy()
            
        self.music_control_frame = tk.Frame(self.root, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        self.music_control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        if not self.audio_available:
            tk.Label(self.music_control_frame, 
                    text="⚠️ 音频系统不可用", 
                    font=("Arial", 10),
                    bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                    fg="red").pack(side=tk.LEFT, padx=5)
            return
            
        # 音乐控制按钮
        if not self.music_playing:
            play_btn = tk.Button(self.music_control_frame, text="▶ 播放音乐", 
                               command=self.play_music,
                               font=("Arial", 10),
                               bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                               fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text'])
        else:
            play_btn = tk.Button(self.music_control_frame, text="⏸ 暂停音乐", 
                               command=self.pause_music,
                               font=("Arial", 10),
                               bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                               fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text'])
        play_btn.pack(side=tk.LEFT, padx=5)
        
        # 导入音乐按钮
        import_btn = tk.Button(self.music_control_frame, text="🎵 导入音乐", 
                             command=self.import_music,
                             font=("Arial", 10),
                             bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                             fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text'])
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 音量控制
        volume_label = tk.Label(self.music_control_frame, text="音量:", 
                              font=("Arial", 10),
                              bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                              fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'])
        volume_label.pack(side=tk.LEFT, padx=5)
        
        volume_scale = ttk.Scale(self.music_control_frame, from_=0, to=1, 
                               orient=tk.HORIZONTAL, length=100,
                               command=self.change_volume)
        volume_scale.set(self.volume)
        volume_scale.pack(side=tk.LEFT, padx=5)

    def create_login_ui(self):
        self.stage = "login"
        self.clear()
        self.create_progress_indicator()
        self.create_music_controls()  # 添加音乐控制面板
        
        # 原有的登录界面内容
        tk.Label(self.root, text="QuizGame 登录", font=("Arial", 20, "bold"), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).pack(pady=20)
        name, time_ = self.quiz.getExamNameAndTime()
        tk.Label(self.root, text=f"测验名称: {name}", font=("Arial", 14), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).pack()
        tk.Label(self.root, text=f"测验时长: {time_} 分钟", font=("Arial", 14), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).pack()
        tk.Label(self.root, text="游戏说明：", font=("Arial", 14, "bold"), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).pack(pady=5)
        text = tk.Text(self.root, height=10, width=80, font=("Arial", 12), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg'], relief="flat")
        text.insert(tk.END, TxtFile.getGameInfo())
        text.config(state="disabled")
        text.pack(pady=10)
        frame = tk.Frame(self.root, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        frame.pack(pady=10)
        tk.Label(frame, text="学号:", font=("Arial", 12), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).grid(row=0, column=0, padx=5)
        self.id_entry = tk.Entry(frame, font=("Arial", 12), relief="solid", bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg'])
        self.id_entry.grid(row=0, column=1)
        tk.Label(frame, text="姓名:", font=("Arial", 12), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).grid(row=1, column=0, padx=5)
        self.name_entry = tk.Entry(frame, font=("Arial", 12), relief="solid", bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg'])
        self.name_entry.grid(row=1, column=1)
        
        # 模式选择
        mode_frame = tk.Frame(self.root, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        mode_frame.pack(pady=10)
        tk.Label(mode_frame, text="选择模式:", font=("Arial", 12), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="simple") # 默认简单模式
        tk.Radiobutton(mode_frame, text="简单模式 (20秒)", variable=self.mode_var, value="simple", 
                      font=("Arial", 12), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'], 
                      fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'], 
                      selectcolor=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg']).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="中等模式 (10秒)", variable=self.mode_var, value="medium", 
                      font=("Arial", 12), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'], 
                      fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'], 
                      selectcolor=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg']).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="困难模式 (5秒)", variable=self.mode_var, value="hard", 
                      font=("Arial", 12), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'], 
                      fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'], 
                      selectcolor=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg']).pack(side=tk.LEFT, padx=5)
        
        tk.Button(self.root, text="登录", font=("Arial", 14), command=self.validate_login, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'], fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text']).pack(pady=20)

    def validate_login(self):
        sid = ''.join(c for c in self.id_entry.get() if c.isdigit())
        sname = self.name_entry.get().strip()
        for student_id, student_name in self.students:
            if student_id == sid and student_name == sname:
                self.student_id = sid
                self.student_name = sname
                self.game_mode = self.mode_var.get() # Set game mode from selection
                self.stage = "select"
                self.start_exam()
                return
        messagebox.showerror("登录失败", 
            f"学号或姓名不正确！\n\n"
            f"你输入的是:\n学号: {self.id_entry.get()}\n姓名: {sname}\n\n"
            f"请检查:\n1. 学号必须是10位数字\n2. 姓名必须完全匹配")

    def start_exam(self):
        self.clear()
        self.create_progress_indicator()
        self.create_score_indicator()
        self.create_music_controls()  # 添加音乐控制面板
        self.time_label = tk.Label(self.root, text="", font=("Arial", 12), bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        self.time_label.pack(side=tk.BOTTOM, pady=5)
        self.timer_running = True
        self.countdown()
        self.show_question()

    def countdown(self):
        if self.time_left > 0 and self.timer_running:
            mins, secs = divmod(self.time_left, 60)
            self.time_label.config(text=f"剩余时间: {mins:02}:{secs:02}")
            self.time_left -= 1
            self.root.after(1000, self.countdown)
        elif self.time_left <= 0:
            self.end_exam()

    def show_question(self):
        self.clear_except_timer()
        self.create_score_indicator()
        self.create_music_controls()  # 添加音乐控制面板
        if self.current_question >= len(self.questions):
            if len(self.wrong_questions) > 0:
                self.show_review_page()
            elif len(self.collected_questions) > 0:
                self.show_collected_page()
            else:
                self.end_exam()
            return
        q = self.questions[self.current_question]
        # stage赋值
        if q['type'] == 'select':
            self.stage = "select"
        elif q['type'] == 'fill':
            self.stage = "fill"
        elif q['type'] == 'tf':
            self.stage = "tf"
        self.create_progress_indicator()
        main_frame = tk.Frame(self.root, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        tk.Label(main_frame, 
                text=f"第 {self.current_question + 1} 题",
                font=("Arial", 16), 
                bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text']).pack(anchor="w", pady=10)
        tk.Label(main_frame, 
                text=q["text"], 
                wraplength=800,
                font=("Arial", 14), 
                bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text']).pack(anchor="w", pady=5)
        self.feedback_label = tk.Label(main_frame, text="", font=("Arial", 12), 
                                     bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                                     fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'])
        self.feedback_label.pack(anchor="w")
        
        # 困难模式计时器
        if self.game_mode != "simple":  # 简单模式不显示计时器
            self.question_time_left = self.mode_times[self.game_mode]
            self.question_timer_label = tk.Label(main_frame, text=f"剩余时间: {self.question_time_left}s", font=("Arial", 14, "bold"), fg="red", bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
            self.question_timer_label.pack(anchor="ne", pady=5)
            self.question_countdown()
            
        options_frame = tk.Frame(main_frame, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        options_frame.pack(anchor="w", pady=10)
        if q["type"] == "select":
            self.selected = tk.StringVar()
            for i, opt in enumerate(q["options"]):
                label = chr(65 + i)
                option_frame = tk.Frame(options_frame, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
                option_frame.pack(anchor="w", fill=tk.X, pady=2)
                rb = tk.Radiobutton(option_frame, variable=self.selected, value=label, 
                                  font=("Arial", 12), 
                                  bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                                  fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'],
                                  selectcolor=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg'])
                rb.pack(side=tk.LEFT)
                option_text = tk.Label(option_frame, text=f"{label}. {opt}", 
                                     wraplength=700, justify=tk.LEFT, 
                                     font=("Arial", 12), 
                                     bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                                     fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'])
                option_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        elif q["type"] == "tf":
            self.selected = tk.StringVar()
            tk.Radiobutton(options_frame, text="对", variable=self.selected, value="对", 
                          font=("Arial", 12), 
                          bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                          fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'],
                          selectcolor=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg']).pack(anchor="w")
            tk.Radiobutton(options_frame, text="错", variable=self.selected, value="错", 
                          font=("Arial", 12), 
                          bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                          fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'],
                          selectcolor=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg']).pack(anchor="w")
        elif q["type"] == "fill":
            self.answer_entry = tk.Entry(options_frame, font=("Arial", 12), width=50, relief="solid",
                                       bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['frame_bg'],
                                       fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text'])
            self.answer_entry.pack(pady=10)
        collect_state = self.is_question_collected(q)
        btn_text = "移除收藏" if collect_state else "收藏题目"
        fav_btn = tk.Button(self.root, text=btn_text, font=("Arial", 12), 
                           bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                           fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text'])
        fav_btn.pack(side=tk.RIGHT, anchor="ne", padx=30, pady=18)
        fav_btn.config(command=lambda: self.toggle_collect_current(q, fav_btn))
        tk.Button(self.root, text="提交答案", command=self.check_answer, 
                 font=("Arial", 12), 
                 bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                 fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text']).pack(side=tk.BOTTOM, pady=20)

    def question_countdown(self):
        """每题倒计时"""
        if self.game_mode != "simple" and self.question_time_left > 0:
            self.question_timer_label.config(text=f"剩余时间: {self.question_time_left}s")
            self.question_time_left -= 1
            self.question_timer_id = self.root.after(1000, self.question_countdown)
        elif self.game_mode != "simple" and self.question_time_left <= 0:
            # 时间到，显示超时提示并进入下一题
            self.question_timer_label.config(text="时间到！", fg="red")
            messagebox.showinfo("超时", "超时啦！")
            self.next_question()  # 自动进入下一题
            
    def is_question_collected(self, q):
        for item in self.collected_questions:
            if item.get("question"):     # 错题形式
                if item["question"] == q:
                    return True
            else: # 正常收藏题
                if item == q:
                    return True
        return False

    def toggle_collect_current(self, q, button):
        existing = None
        for item in self.collected_questions:
            if (item.get("question", None) and item["question"] == q) or item == q:
                existing = item
                break
        if existing:
            if messagebox.askyesno("移除收藏", "确定要移除该题的收藏？"):
                self.collected_questions.remove(existing)
                button.config(text="收藏题目")
                self.create_score_indicator()
                return
        else:
            match = None
            for wrong in self.wrong_questions:
                if wrong["question"] == q:
                    match = wrong
                    break
            self.collected_questions.append(match if match else q)
            button.config(text="移除收藏")
            messagebox.showinfo("提示", "题目已收藏！")
        self.create_score_indicator()
        
    def play_sound(self, sound_type):
        """播放音效"""
        def play():
            if sound_type == "correct":
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            else:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
        threading.Thread(target=play, daemon=True).start()

    def check_answer(self):
        q = self.questions[self.current_question]
        if q["type"] in ["select", "tf"]:
            user_ans = self.selected.get()
            if not user_ans:
                messagebox.showwarning("提示", "请选择答案！")
                return
        else:
            user_ans = self.answer_entry.get().strip()
            if not user_ans:
                messagebox.showwarning("提示", "请输入答案！")
                return
                
        # Cancel question timer if in hard mode
        if self.game_mode != "simple" and self.question_timer_id is not None:
            self.root.after_cancel(self.question_timer_id)
            self.question_timer_id = None # Reset timer ID

        # 更新题型统计
        self.question_stats[q['type']]['total'] += 1
        if user_ans == q["answer"]:
            self.score += q["score"]
            self.feedback_label.config(text="✔ 正确", fg="green")
            self.play_sound("correct")
            self.question_stats[q['type']]['correct'] += 1
        else:
            self.feedback_label.config(
                text=f"✘ 错误\n正确答案: {q['answer']}\n解析: {q['explanation']}", 
                fg="red")
            self.play_sound("wrong")
            self.wrong_questions.append({"question": q, "user_answer": user_ans})
        self.create_score_indicator()
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "提交答案":
                widget.destroy()
        tk.Button(self.root, text="下一题", command=self.next_question, font=("Arial", 12), bg="#2196F3", fg="white").pack(side=tk.BOTTOM, pady=20)

    def next_question(self):
        # Cancel question timer if in hard mode
        if self.game_mode != "simple" and self.question_timer_id is not None:
            self.root.after_cancel(self.question_timer_id)
            self.question_timer_id = None # Reset timer ID
        self.current_question += 1
        self.show_question()

    def show_review_page(self):
        # Cancel question timer if in hard mode
        if self.game_mode != "simple" and self.question_timer_id is not None:
            self.root.after_cancel(self.question_timer_id)
            self.question_timer_id = None # Reset timer ID
        """显示错题回顾页面"""
        self.stage = "review"
        self.clear()
        self.create_progress_indicator()
        self.create_music_controls()  # 添加音乐控制面板
        
        # 创建分析框架
        analysis_frame = tk.Frame(self.root, bg="#e6f3ff", padx=20, pady=10)
        analysis_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(analysis_frame, text="答题分析", font=("Arial", 16, "bold"), bg="#e6f3ff").pack(anchor="w")
        
        # 计算各题型正确率
        for q_type, stats in self.question_stats.items():
            if stats['total'] > 0:
                correct_rate = (stats['correct'] / stats['total']) * 100
                type_name = {
                    'select': '选择题',
                    'fill': '填空题',
                    'tf': '判断题'
                }[q_type]
                
                frame = tk.Frame(analysis_frame, bg="#e6f3ff")
                frame.pack(fill="x", pady=2)
                
                # 创建进度条
                progress = ttk.Progressbar(frame, length=200, mode='determinate')
                progress['value'] = correct_rate
                progress.pack(side="left", padx=5)
                
                # 显示具体数据
                text = f"{type_name}: {stats['correct']}/{stats['total']} ({correct_rate:.1f}%)"
                tk.Label(frame, text=text, font=("Arial", 12), bg="#e6f3ff").pack(side="left", padx=5)
        
        # 显示错题列表
        tk.Label(self.root, text="错题回顾", font=("Arial", 18, "bold"), bg="#e6f3ff").pack(pady=10, fill="x")
        
        canvas = tk.Canvas(self.root, bg="#ffffff", height=400)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", on_configure)
        
        canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        for i, item in enumerate(self.wrong_questions):
            q = item["question"]
            user_answer = item.get("user_answer", "")
            
            frame = tk.Frame(scrollable_frame, borderwidth=2, relief="groove", padx=15, pady=15, bg="#f9f9f9")
            frame.pack(fill="x", padx=12, pady=10)
            
            # 显示题型
            type_name = {
                'select': '选择题',
                'fill': '填空题',
                'tf': '判断题'
            }[q['type']]
            
            tk.Label(frame, text=f"{type_name} {i+1}", font=("Arial", 14, "bold"), bg="#f9f9f9").pack(anchor="w")
            tk.Label(frame, text=q["text"], wraplength=700, font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=5)
            
            if q["type"] == "select":
                options = "\n".join([f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])])
                tk.Label(frame, text=f"选项:\n{options}", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=5)
                
            tk.Label(frame, text=f"你的答案: {user_answer}", fg="red", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=2)
            tk.Label(frame, text=f"正确答案: {q['answer']}", fg="green", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=2)
            tk.Label(frame, text=f"解析: {q['explanation']}", font=("Arial", 12, "italic"), bg="#f9f9f9").pack(anchor="w", pady=2)
            
            # 添加收藏按钮
            collect_btn = tk.Button(frame, text="收藏题目", font=("Arial", 10), bg="#FF9800", fg="white")
            collect_btn.config(command=lambda t=q, btn=collect_btn: self.toggle_collect_current(t, btn))
            collect_btn.pack(anchor="e", pady=5)
        
        # 添加按钮框架
        button_frame = tk.Frame(self.root, bg="#e6f3ff")
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        # 如果有收藏的题目，显示查看收藏集按钮
        if len(self.collected_questions) > 0:
            tk.Button(button_frame, text="查看收藏集", command=self.show_collected_page, 
                     font=("Arial", 12), bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=10)
        
        # 显示查看成绩按钮
        tk.Button(button_frame, text="查看成绩", command=self.end_exam, 
                 font=("Arial", 12), bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=10)
        
        self.create_score_indicator()

    def show_collected_page(self):
        # Cancel question timer if in hard mode
        if self.game_mode != "simple" and self.question_timer_id is not None:
            self.root.after_cancel(self.question_timer_id)
            self.question_timer_id = None # Reset timer ID
        self.stage = "review"
        self.clear()
        self.create_progress_indicator()
        self.create_music_controls()  # 添加音乐控制面板
        
        # 创建分析框架
        analysis_frame = tk.Frame(self.root, bg="#e6f3ff", padx=20, pady=10)
        analysis_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(analysis_frame, text="答题分析", font=("Arial", 16, "bold"), bg="#e6f3ff").pack(anchor="w")
        
        # 计算各题型正确率
        for q_type, stats in self.question_stats.items():
            if stats['total'] > 0:
                correct_rate = (stats['correct'] / stats['total']) * 100
                type_name = {
                    'select': '选择题',
                    'fill': '填空题',
                    'tf': '判断题'
                }[q_type]
                
                frame = tk.Frame(analysis_frame, bg="#e6f3ff")
                frame.pack(fill="x", pady=2)
                
                # 创建进度条
                progress = ttk.Progressbar(frame, length=200, mode='determinate')
                progress['value'] = correct_rate
                progress.pack(side="left", padx=5)
                
                # 显示具体数据
                text = f"{type_name}: {stats['correct']}/{stats['total']} ({correct_rate:.1f}%)"
                tk.Label(frame, text=text, font=("Arial", 12), bg="#e6f3ff").pack(side="left", padx=5)
        
        # 显示错题列表
        tk.Label(self.root, text="错题回顾", font=("Arial", 18, "bold"), bg="#e6f3ff").pack(pady=10, fill="x")
        
        canvas = tk.Canvas(self.root, bg="#ffffff", height=400)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", on_configure)
        
        canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        for i, item in enumerate(self.collected_questions):
            if isinstance(item, dict) and item.get("question"):
                q = item["question"]
                user_answer = item.get("user_answer", "")
            else:
                q = item
                user_answer = ""
                
            frame = tk.Frame(scrollable_frame, borderwidth=2, relief="groove", padx=15, pady=15, bg="#f9f9f9")
            frame.pack(fill="x", padx=12, pady=10)
            
            # 显示题型
            type_name = {
                'select': '选择题',
                'fill': '填空题',
                'tf': '判断题'
            }[q['type']]
            
            tk.Label(frame, text=f"{type_name} {i+1}", font=("Arial", 14, "bold"), bg="#f9f9f9").pack(anchor="w")
            tk.Label(frame, text=q["text"], wraplength=700, font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=5)
            
            if q["type"] == "select":
                options = "\n".join([f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])])
                tk.Label(frame, text=f"选项:\n{options}", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=5)
                
            if user_answer:
                tk.Label(frame, text=f"你的答案: {user_answer}", fg="red", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=2)
            tk.Label(frame, text=f"正确答案: {q['answer']}", fg="green", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=2)
            tk.Label(frame, text=f"解析: {q['explanation']}", font=("Arial", 12, "italic"), bg="#f9f9f9").pack(anchor="w", pady=2)
            
            collect_btn = tk.Button(frame, text="移除收藏", font=("Arial", 10), bg="#F44336", fg="white")
            collect_btn.config(command=lambda t=item, btn=collect_btn: self.remove_from_collection_in_collected(t))
            collect_btn.pack(anchor="e", pady=5)
            
        tk.Button(self.root, text="查看成绩", command=self.end_exam, font=("Arial", 12), bg="#2196F3", fg="white").pack(side=tk.BOTTOM, pady=20)
        self.create_score_indicator()

    def remove_from_collection_in_collected(self, t):
        if messagebox.askyesno("移除收藏", "确定要移除该题的收藏？"):
            self.collected_questions.remove(t)
            messagebox.showinfo("提示", "该题已从收藏集中移除。")
            if len(self.collected_questions) == 0:
                self.end_exam()
            else:
                self.show_collected_page()
            self.create_score_indicator()

    def show_collected(self):
        if len(self.collected_questions) == 0:
            messagebox.showinfo("提示", "你还没有收藏任何题目~")
            return
        win = tk.Toplevel(self.root)
        win.title("收藏集")
        win.geometry("800x700")
        tk.Label(win, text="我的收藏集", font=("Arial", 18, "bold"), bg="#e6f3ff").pack(pady=10, fill="x")
        canvas = tk.Canvas(win, bg="#ffffff", height=600)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", on_configure)
        canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        for i, item in enumerate(self.collected_questions):
            if isinstance(item, dict) and item.get("question"):
                q = item["question"]
                user_answer = item.get("user_answer", "")
            else:
                q = item
                user_answer = ""
            frame = tk.Frame(scrollable_frame, borderwidth=2, relief="groove", padx=15, pady=15, bg="#f9f9f9")
            frame.pack(fill="x", padx=12, pady=10)
            tk.Label(frame, text=f"收藏题 {i+1}", font=("Arial", 14, "bold"), bg="#f9f9f9").pack(anchor="w")
            tk.Label(frame, text=q["text"], wraplength=700, font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=5)
            if q["type"] == "select":
                options = "\n".join([f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])])
                tk.Label(frame, text=f"选项:\n{options}", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=5)
            if user_answer:
                tk.Label(frame, text=f"你的答案: {user_answer}", fg="red", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=2)
            tk.Label(frame, text=f"正确答案: {q['answer']}", fg="green", font=("Arial", 12), bg="#f9f9f9").pack(anchor="w", pady=2)
            tk.Label(frame, text=f"解析: {q['explanation']}", font=("Arial", 12, "italic"), bg="#f9f9f9").pack(anchor="w", pady=2)
            collect_btn = tk.Button(frame, text="移除收藏", font=("Arial", 10), bg="#F44336", fg="white")
            collect_btn.config(command=lambda t=item, btn=collect_btn: self.remove_from_collection(t, win))
            collect_btn.pack(anchor="e", pady=5)

    def remove_from_collection(self, t, container_win):
        if messagebox.askyesno("移除收藏", "确定要移除该题的收藏？"):
            self.collected_questions.remove(t)
            messagebox.showinfo("提示", "该题已从收藏集中移除。")
            if hasattr(self, "fav_btn") and self.fav_btn.winfo_exists() and len(self.collected_questions)==0:
                self.fav_btn.destroy()
                self.fav_btn = None
            container_win.destroy()
            if len(self.collected_questions) > 0:
                self.show_collected()
            self.create_score_indicator()

    def end_exam(self):
        # Cancel question timer if in hard mode
        if self.game_mode != "simple" and self.question_timer_id is not None:
            self.root.after_cancel(self.question_timer_id)
            self.question_timer_id = None # Reset timer ID
        self.stage = "end"
        self.timer_running = False
        self.clear()
        self.create_music_controls()  # 添加音乐控制面板
        
        # 创建结果框架
        result_frame = tk.Frame(self.root, bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
        result_frame.pack(pady=20)
        
        # 显示成绩
        tk.Label(result_frame, 
                text=f"测验结束！{self.student_name}同学的总得分：{self.score}", 
                font=("Arial", 18, "bold"),
                bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'],
                fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['text']).pack()
        
        # 显示最高分信息
        max_score = TxtFile.getMaxScore()
        if self.score > max_score:
            TxtFile.setNewRecord(self.student_id, self.student_name, self.score)
            tk.Label(result_frame, 
                    text="🎉 恭喜你打破最高分记录！", 
                    fg="green", 
                    font=("Arial", 14),
                    bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).pack()
        else:
            tk.Label(result_frame,
                    text=f"当前最高分: {max_score}\n对不起，你没有创造新的得分纪录！\n下次再努力哦！谢谢！",
                    fg="blue",
                    font=("Arial", 12),
                    bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['bg']).pack()
                    
        tk.Button(self.root, 
                 text="退出", 
                 command=self.root.quit, 
                 font=("Arial", 12), 
                 bg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button'],
                 fg=self.theme_colors['dark' if self.is_dark_mode else 'light']['button_text']).pack(pady=20)

    def create_default_correct_sound(self):
        """创建一个简单的正确音效"""
        sample_rate = 44100
        duration = 0.5  # 秒
        frequency = 880  # Hz
        
        # 生成一个简单的正弦波
        t = numpy.linspace(0, duration, int(sample_rate * duration), False)
        tone = numpy.sin(frequency * t * 2 * numpy.pi)
        
        # 转换为16位整数
        tone = (tone * 32767).astype(numpy.int16)
        
        # 创建Sound对象
        return pygame.mixer.Sound(buffer=tone.tobytes())

    def create_default_wrong_sound(self):
        """创建一个简单的错误音效"""
        sample_rate = 44100
        duration = 0.5  # 秒
        frequency = 440  # Hz
        
        # 生成一个简单的正弦波
        t = numpy.linspace(0, duration, int(sample_rate * duration), False)
        tone = numpy.sin(frequency * t * 2 * numpy.pi)
        
        # 转换为16位整数
        tone = (tone * 32767).astype(numpy.int16)
        
        # 创建Sound对象
        return pygame.mixer.Sound(buffer=tone.tobytes())

    def apply_theme(self):
        """应用当前主题到所有窗口"""
        theme = self.theme_colors['dark' if self.is_dark_mode else 'light']
        
        # 设置根窗口背景
        if self.current_bg_image:
            self.root.configure(bg=theme['bg'])
        else:
            self.root.configure(bg=theme['bg'])
            
        # 更新所有现有组件的样式
        for widget in self.root.winfo_children():
            self.update_widget_theme(widget, theme)
            
    def update_widget_theme(self, widget, theme):
        """递归更新组件及其子组件的主题"""
        if isinstance(widget, (tk.Frame, tk.LabelFrame)):
            widget.configure(bg=theme['bg'])
        elif isinstance(widget, tk.Label):
            widget.configure(bg=theme['bg'], fg=theme['text'])
        elif isinstance(widget, tk.Button):
            widget.configure(bg=theme['button'], fg=theme['button_text'])
        elif isinstance(widget, tk.Text):
            widget.configure(bg=theme['frame_bg'], fg=theme['text'])
        elif isinstance(widget, tk.Entry):
            widget.configure(bg=theme['frame_bg'], fg=theme['text'])
            
        # 递归更新子组件
        for child in widget.winfo_children():
            self.update_widget_theme(child, theme)
            
    def toggle_theme(self):
        """切换深浅色模式"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        
    def import_background(self):
        """导入背景图片"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择背景图片",
                filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp")]
            )
            
            if not file_path:  # 用户取消选择
                return
                
            # 加载并调整图片大小
            image = Image.open(file_path)
            # 保持图片比例
            width, height = image.size
            ratio = min(900/width, 750/height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 创建新的图片作为背景
            bg_image = Image.new('RGB', (900, 750), self.theme_colors['dark' if self.is_dark_mode else 'light']['bg'])
            # 将调整后的图片居中放置
            offset = ((900 - new_size[0]) // 2, (750 - new_size[1]) // 2)
            bg_image.paste(image, offset)
            
            self.current_bg_image = ImageTk.PhotoImage(bg_image)
            self.bg_image_path = file_path
            
            # 创建或更新背景标签
            if hasattr(self, 'bg_label') and self.bg_label is not None:
                self.bg_label.destroy()
            self.bg_label = tk.Label(self.root, image=self.current_bg_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.bg_label.lower()  # 将背景置于底层
            
            # 重新创建当前页面的内容
            if self.stage == "login":
                self.create_login_ui()
            elif self.stage in ["select", "fill", "tf"]:
                self.show_question()
            elif self.stage == "review":
                self.show_review_page()
            elif self.stage == "collected":
                self.show_collected_page()
            elif self.stage == "end":
                self.end_exam()
            
            # 应用当前主题
            self.apply_theme()
            
        except Exception as e:
            messagebox.showerror("错误", f"无法加载背景图片: {str(e)}\n请确保选择了有效的图片文件。")
            
    def remove_background(self):
        """移除背景图片"""
        try:
            if hasattr(self, 'bg_label') and self.bg_label is not None:
                self.bg_label.destroy()
                self.bg_label = None
            self.current_bg_image = None
            self.bg_image_path = None
            
            # 重新创建当前页面的内容
            if self.stage == "login":
                self.create_login_ui()
            elif self.stage in ["select", "fill", "tf"]:
                self.show_question()
            elif self.stage == "review":
                self.show_review_page()
            elif self.stage == "collected":
                self.show_collected_page()
            elif self.stage == "end":
                self.end_exam()
                
            self.apply_theme()
        except Exception as e:
            messagebox.showerror("错误", f"移除背景图片时出错: {str(e)}")

    def import_music(self):
        """导入音乐文件"""
        if not self.audio_available:
            messagebox.showwarning("警告", "音频系统不可用，无法导入音乐。")
            return
            
        file_path = filedialog.askopenfilename(
            title="选择音乐文件",
            filetypes=[("音频文件", "*.mp3 *.wav")]
        )
        
        if file_path:
            try:
                # 停止当前播放的音乐
                if self.music_playing:
                    pygame.mixer.music.stop()
                    self.music_playing = False
                
                # 加载新的音乐
                pygame.mixer.music.load(file_path)
                self.current_music = file_path
                
                # 设置音量
                pygame.mixer.music.set_volume(self.volume)
                
                # 开始播放
                pygame.mixer.music.play(-1)  # -1表示循环播放
                self.music_playing = True
                
                # 更新控制面板
                self.create_music_controls()
                
            except Exception as e:
                messagebox.showerror("错误", f"无法加载音乐文件: {str(e)}")

    def play_music(self):
        """播放音乐"""
        if not self.audio_available:
            messagebox.showwarning("警告", "音频系统不可用，无法播放音乐。")
            return
            
        if self.current_music and not self.music_playing:
            try:
                pygame.mixer.music.play(-1)
                self.music_playing = True
                self.create_music_controls()
            except Exception as e:
                messagebox.showerror("错误", f"播放音乐失败: {str(e)}")

    def pause_music(self):
        """暂停音乐"""
        if not self.audio_available:
            return
            
        if self.music_playing:
            pygame.mixer.music.pause()
            self.music_playing = False
            self.create_music_controls()

    def change_volume(self, value):
        """改变音量"""
        if not self.audio_available:
            return
            
        try:
            self.volume = float(value)
            pygame.mixer.music.set_volume(self.volume)
        except Exception as e:
            print(f"调整音量时出错: {str(e)}")

if __name__ == "__main__":
    app = QuizGame()
    app.root.mainloop()