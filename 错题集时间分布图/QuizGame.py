import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
from Exam import TxtFile, Stu, QusAndAns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class QuizGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QuizGame 测验系统")
        self.root.geometry("900x750")
        
        # 初始化属性
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
        self.stage = "login"
        self.question_start_time = 0  # 记录每道题开始时间
        self.question_times = []  # 记录每道题花费的时间
        
        try:
            # 加载学生数据
            self.students = Stu().getstu()
            print("加载的学生数据:")
            for i, (sid, sname) in enumerate(self.students[:10]):
                print(f"{i+1}. 学号: {sid}, 姓名: {sname}")
            
            # 加载题库
            self.quiz = QusAndAns()
            all_questions = self.quiz.getQuestions()
            
            # 分离题目类型
            select_questions = [q for q in all_questions if q['type'] == 'select'][:5]
            fill_questions = [q for q in all_questions if q['type'] == 'fill'][:5]
            tf_questions = [q for q in all_questions if q['type'] == 'tf'][:5]
            
            # 组合题目顺序
            self.questions = select_questions + fill_questions + tf_questions
            self.time_left = self.quiz.examTime * 60
            
        except Exception as e:
            messagebox.showerror("初始化错误", f"初始化失败: {str(e)}")
            self.root.destroy()
            return
            
        self.create_login_ui()

    def clear(self):
        """清除所有窗口组件"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_except_timer(self):
        """清除除计时器和进度条外的所有组件"""
        for widget in self.root.winfo_children():
            if widget not in [self.time_label, self.score_label, self.progress_frame]:
                widget.destroy()

    def create_progress_indicator(self):
        """创建右上角的进度指示器"""
        if self.progress_frame:
            self.progress_frame.destroy()
            
        self.progress_frame = tk.Frame(self.root)
        self.progress_frame.pack(side=tk.TOP, anchor="ne", padx=10, pady=10)
        
        stages = ["登录", "选择题", "填空题", "判断题", "时间花费分布"]
        self.progress_labels = []
        
        for i, stage in enumerate(stages):
            if (self.stage == "login" and i == 0) or \
               (self.stage == "select" and i == 1) or \
               (self.stage == "fill" and i == 2) or \
               (self.stage == "tf" and i == 3) or \
               (self.stage == "review" and i == 4):
                fg = "red"
                font = ("Arial", 10, "bold")
            else:
                fg = "gray"
                font = ("Arial", 10)
                
            label = tk.Label(self.progress_frame, text=stage, fg=fg, font=font)
            label.grid(row=0, column=i, padx=5)
            self.progress_labels.append(label)

    def create_score_indicator(self):
        """创建得分显示"""
        if hasattr(self, 'score_label') and self.score_label is not None:
            self.score_label.destroy()
        self.score_label = tk.Label(self.root, text=f"当前得分: {self.score}", 
                                  font=("Arial", 12, "bold"), fg="blue")
        self.score_label.pack(side=tk.TOP, anchor="ne", padx=10, pady=5)

    def create_login_ui(self):
        """创建登录界面"""
        self.stage = "login"
        self.clear()
        self.create_progress_indicator()
        
        tk.Label(self.root, text="QuizGame 登录", font=("Arial", 20, "bold")).pack(pady=20)

        name, time_ = self.quiz.getExamNameAndTime()
        tk.Label(self.root, text=f"测验名称: {name}", font=("Arial", 14)).pack()
        tk.Label(self.root, text=f"测验时长: {time_} 分钟", font=("Arial", 14)).pack()

        tk.Label(self.root, text="游戏说明：", font=("Arial", 14, "bold")).pack(pady=5)
        text = tk.Text(self.root, height=10, width=80, font=("Arial", 12))
        text.insert(tk.END, TxtFile.getGameInfo())
        text.config(state="disabled")
        text.pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        tk.Label(frame, text="学号:", font=("Arial", 12)).grid(row=0, column=0, padx=5)
        self.id_entry = tk.Entry(frame, font=("Arial", 12))
        self.id_entry.grid(row=0, column=1)

        tk.Label(frame, text="姓名:", font=("Arial", 12)).grid(row=1, column=0, padx=5)
        self.name_entry = tk.Entry(frame, font=("Arial", 12))
        self.name_entry.grid(row=1, column=1)

        tk.Button(self.root, text="登录", font=("Arial", 14), command=self.validate_login).pack(pady=20)

    def validate_login(self):
        """验证登录信息"""
        sid = ''.join(c for c in self.id_entry.get() if c.isdigit())
        sname = self.name_entry.get().strip()
        
        print(f"\n尝试登录: 学号={sid}, 姓名={sname}")
        print("有效学生列表:")
        for i, (student_id, student_name) in enumerate(self.students):
            print(f"{i+1}. {student_id}: {student_name}")
        
        # 检查匹配
        for student_id, student_name in self.students:
            if student_id == sid and student_name == sname:
                self.student_id = sid
                self.student_name = sname
                self.stage = "select"
                self.start_exam()
                return
                
        messagebox.showerror("登录失败", 
            f"学号或姓名不正确！\n\n"
            f"你输入的是:\n学号: {self.id_entry.get()}\n姓名: {sname}\n\n"
            f"请检查:\n1. 学号必须是10位数字\n2. 姓名必须完全匹配")

    def start_exam(self):
        """开始考试"""
        self.clear()
        self.create_progress_indicator()
        self.create_score_indicator()
        self.time_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.time_label.pack(side=tk.BOTTOM, pady=5)
        self.timer_running = True
        self.countdown()
        # 重置时间记录
        self.question_times = []
        self.show_question()

    def countdown(self):
        """倒计时功能"""
        if not hasattr(self, 'time_label') or not self.time_label.winfo_exists():
            return
        if self.time_left > 0 and self.timer_running:
            mins, secs = divmod(self.time_left, 60)
            self.time_label.config(text=f"剩余时间: {mins:02}:{secs:02}")
            self.time_left -= 1
            self.root.after(1000, self.countdown)
        elif self.time_left <= 0:
            self.end_exam()

    def show_question(self):
        """显示当前问题"""
        self.clear_except_timer()
        self.create_score_indicator()
        
        if self.current_question >= len(self.questions):
            self.show_review()
            return

        # 记录开始时间
        self.question_start_time = time.time()

        q = self.questions[self.current_question]
        if q['type'] == 'select':
            self.stage = "select"
        elif q['type'] == 'fill':
            self.stage = "fill"
        elif q['type'] == 'tf':
            self.stage = "tf"
        self.create_progress_indicator()

        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 题目信息
        tk.Label(main_frame, 
                text=f"第 {self.current_question + 1} 题 ({q['type']})",
                font=("Arial", 16)).pack(anchor="w", pady=10)
        tk.Label(main_frame, 
                text=q["text"], 
                wraplength=800,
                font=("Arial", 14)).pack(anchor="w", pady=5)

        self.feedback_label = tk.Label(main_frame, text="", font=("Arial", 12))
        self.feedback_label.pack(anchor="w")

        # 选项框架
        options_frame = tk.Frame(main_frame)
        options_frame.pack(anchor="w", pady=10)

        if q["type"] == "select":
            self.selected = tk.StringVar()
            for i, opt in enumerate(q["options"]):
                label = chr(65 + i)
                # 创建框架包含单选框和标签
                option_frame = tk.Frame(options_frame)
                option_frame.pack(anchor="w", fill=tk.X, pady=2)
                
                # 单选框
                rb = tk.Radiobutton(option_frame, 
                                  variable=self.selected,
                                  value=label,
                                  font=("Arial", 12))
                rb.pack(side=tk.LEFT)
                
                # 可换行的选项文本
                option_text = tk.Label(option_frame, 
                                     text=f"{label}. {opt}",
                                     wraplength=700,
                                     justify=tk.LEFT,
                                     font=("Arial", 12))
                option_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # 添加键盘绑定
                self.root.bind(label.lower(), lambda e, val=label: self.selected.set(val))
                self.root.bind(label.upper(), lambda e, val=label: self.selected.set(val))
                
        elif q["type"] == "tf":
            self.selected = tk.StringVar()
            tk.Radiobutton(options_frame, 
                          text="对",
                          variable=self.selected,
                          value="对",
                          font=("Arial", 12)).pack(anchor="w")
            tk.Radiobutton(options_frame, 
                          text="错",
                          variable=self.selected,
                          value="错",
                          font=("Arial", 12)).pack(anchor="w")
        elif q["type"] == "fill":
            self.answer_entry = tk.Entry(options_frame, 
                                      font=("Arial", 12),
                                      width=50)
            self.answer_entry.pack(pady=10)
            # 为填空题输入框设置焦点
            self.answer_entry.focus_set()

        # 提交按钮
        submit_button = tk.Button(self.root, 
                text="提交答案",
                command=self.check_answer,
                font=("Arial", 12))
        submit_button.pack(side=tk.BOTTOM, pady=20)
        
        # 绑定回车键
        self.root.bind('<Return>', lambda e: self.handle_enter_key())

    def handle_enter_key(self):
        """处理回车键事件"""
        if hasattr(self, 'feedback_label') and self.feedback_label.cget("text"):
            # 如果已经显示了反馈信息，按回车键进入下一题
            self.next_question()
        else:
            # 否则提交答案
            self.check_answer()

    def check_answer(self):
        """检查答案"""
        # 计算答题时间
        time_spent = time.time() - self.question_start_time
        self.question_times.append(time_spent)

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

        if user_ans == q["answer"]:
            self.score += q["score"]
            self.feedback_label.config(text="✔ 正确", fg="green")
        else:
            self.feedback_label.config(
                text=f"✘ 错误\n正确答案: {q['answer']}\n解析: {q['explanation']}", 
                fg="red")
            self.wrong_questions.append({
                "question": q,
                "user_answer": user_ans,
                "time_spent": time_spent
            })

        self.create_score_indicator()

        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "提交答案":
                widget.destroy()
                
        next_button = tk.Button(self.root, 
                text="下一题",
                command=self.next_question,
                font=("Arial", 12))
        next_button.pack(side=tk.BOTTOM, pady=20)
        
        # 设置焦点到下一题按钮
        next_button.focus_set()

    def next_question(self):
        """显示下一题"""
        self.current_question += 1
        self.show_question()

    def show_review(self):
        """显示时间分布"""
        self.stage = "review"
        self.clear()
        self.create_progress_indicator()
        
        # 创建主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 时间分布标题
        tk.Label(main_frame,
                text="时间花费分布",
                font=("Arial", 16, "bold")).pack(pady=10)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # 显示所有题目的时间
        question_numbers = range(1, len(self.question_times) + 1)
        bars = ax.bar(question_numbers, self.question_times)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        
        ax.set_xlabel('题号')
        ax.set_ylabel('答题时间（秒）')
        ax.set_title('每题答题时间分布')
        
        # 设置x轴刻度
        ax.set_xticks(question_numbers)
        ax.set_xticklabels([f'第{i}题' for i in question_numbers], rotation=45)
        
        # 在柱子上显示具体数值
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}s',
                    ha='center', va='bottom')
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 调整布局
        plt.tight_layout()
        
        # 将图表嵌入到tkinter窗口
        canvas = FigureCanvasTkAgg(fig, master=main_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 将按钮放在底部
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        tk.Button(button_frame, 
                text="查看成绩",
                command=self.end_exam,
                font=("Arial", 12)).pack(pady=5)

    def end_exam(self):
        """结束考试"""
        self.stage = "end"
        self.timer_running = False
        self.clear()
        
        tk.Label(self.root, 
                text=f"测验结束！{self.student_name}同学的总得分：{self.score}",
                font=("Arial", 18)).pack(pady=20)

        max_score = TxtFile.getMaxScore()
        if self.score > max_score:
            TxtFile.setNewRecord(self.student_id, self.student_name, self.score)
            tk.Label(self.root, 
                    text="🎉 恭喜你打破最高分记录！",
                    fg="green",
                    font=("Arial", 14)).pack()
        else:
            tk.Label(self.root, 
                    text=f"当前最高分: {max_score}\n对不起，你没有创造新的得分纪录！\n下次再努力哦！谢谢！",
                    fg="blue",
                    font=("Arial", 12)).pack()

        tk.Button(self.root, 
                text="退出",
                command=self.root.quit,
                font=("Arial", 12)).pack(pady=20)

if __name__ == "__main__":
    app = QuizGame()
    app.root.mainloop()