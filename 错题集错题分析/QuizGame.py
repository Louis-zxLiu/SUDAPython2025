import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
from Exam import TxtFile, Stu, QusAndAns

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
        # 新增：记录每道题的开始时间
        self.question_start_time = 0
        # 新增：记录每道题花费的时间
        self.question_times = []
        
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
        
        stages = ["登录", "选择题", "填空题", "判断题", "错题回顾", "错题分析"]
        self.progress_labels = []
        
        for i, stage in enumerate(stages):
            if (self.stage == "login" and i == 0) or \
               (self.stage == "select" and i == 1) or \
               (self.stage == "fill" and i == 2) or \
               (self.stage == "tf" and i == 3) or \
               (self.stage == "review" and i == 4) or \
               (self.stage == "analysis" and i == 5):
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
        self.show_question()

    def countdown(self):
        """倒计时功能"""
        if not self.timer_running:
            return
            
        if self.time_left > 0:
            mins, secs = divmod(self.time_left, 60)
            if hasattr(self, 'time_label') and self.time_label.winfo_exists():
                self.time_label.config(text=f"剩余时间: {mins:02}:{secs:02}")
            self.time_left -= 1
            self.root.after(1000, self.countdown)
        else:
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

        # 提交按钮
        tk.Button(self.root, 
                text="提交答案",
                command=self.check_answer,
                font=("Arial", 12)).pack(side=tk.BOTTOM, pady=20)

    def check_answer(self):
        """检查答案"""
        q = self.questions[self.current_question]
        
        # 计算答题时间
        time_spent = round(time.time() - self.question_start_time, 1)
        self.question_times.append(time_spent)
        
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
                
        tk.Button(self.root, 
                text="下一题",
                command=self.next_question,
                font=("Arial", 12)).pack(side=tk.BOTTOM, pady=20)

    def next_question(self):
        """显示下一题"""
        self.current_question += 1
        self.show_question()

    def show_review(self):
        """显示错题回顾"""
        self.stage = "review"
        self.clear()
        self.create_progress_indicator()
        
        if not self.wrong_questions:
            tk.Label(self.root, 
                    text="恭喜！本次测验没有错题！",
                    font=("Arial", 16)).pack(pady=20)
        else:
            tk.Label(self.root, 
                    text="错题回顾",
                    font=("Arial", 16, "bold")).pack(pady=10)
            
            canvas = tk.Canvas(self.root)
            scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            for i, wrong in enumerate(self.wrong_questions):
                q = wrong["question"]
                frame = tk.Frame(scrollable_frame, borderwidth=1, relief="solid", padx=10, pady=10)
                frame.pack(fill="x", padx=10, pady=5)
                
                tk.Label(frame, 
                        text=f"错题 {i+1} ({q['type']})",
                        font=("Arial", 14, "bold")).pack(anchor="w")
                tk.Label(frame, 
                        text=q["text"],
                        wraplength=700,
                        font=("Arial", 12)).pack(anchor="w")
                
                if q["type"] == "select":
                    options = "\n".join([f"{chr(65+j)}. {opt}" for j, opt in enumerate(q["options"])])
                    tk.Label(frame, 
                            text=f"选项:\n{options}",
                            font=("Arial", 12)).pack(anchor="w")
                
                tk.Label(frame, 
                        text=f"你的答案: {wrong['user_answer']}",
                        fg="red",
                        font=("Arial", 12)).pack(anchor="w")
                tk.Label(frame, 
                        text=f"正确答案: {q['answer']}",
                        fg="green",
                        font=("Arial", 12)).pack(anchor="w")
                tk.Label(frame, 
                        text=f"解析: {q['explanation']}",
                        font=("Arial", 12)).pack(anchor="w")
                tk.Label(frame,
                        text=f"用时: {wrong['time_spent']} 秒",
                        font=("Arial", 12)).pack(anchor="w")

        tk.Button(self.root, 
                text="查看错题分析",
                command=self.show_analysis,
                font=("Arial", 12)).pack(side=tk.BOTTOM, pady=20)

    def show_analysis(self):
        """显示错题分析"""
        self.stage = "analysis"
        self.clear()
        self.create_progress_indicator()
        
        tk.Label(self.root, 
                text="错题分析",
                font=("Arial", 16, "bold")).pack(pady=10)
        
        # 计算各题型的错误率
        total_questions = len(self.questions)
        wrong_by_type = {"select": 0, "fill": 0, "tf": 0}
        time_by_type = {"select": [], "fill": [], "tf": []}
        
        for wrong in self.wrong_questions:
            q_type = wrong["question"]["type"]
            wrong_by_type[q_type] += 1
            time_by_type[q_type].append(wrong["time_spent"])
        
        # 显示错误率
        analysis_frame = tk.Frame(self.root)
        analysis_frame.pack(pady=10)
        
        tk.Label(analysis_frame,
                text="各题型错误率：",
                font=("Arial", 14, "bold")).pack(anchor="w")
        
        for q_type in ["select", "fill", "tf"]:
            total = len([q for q in self.questions if q["type"] == q_type])
            wrong = wrong_by_type[q_type]
            error_rate = (wrong / total * 100) if total > 0 else 0
            tk.Label(analysis_frame,
                    text=f"{q_type.upper()}题: {error_rate:.1f}% ({wrong}/{total})",
                    font=("Arial", 12)).pack(anchor="w")
        
        # 显示平均用时
        tk.Label(analysis_frame,
                text="\n各题型平均用时：",
                font=("Arial", 14, "bold")).pack(anchor="w")
        
        for q_type in ["select", "fill", "tf"]:
            times = time_by_type[q_type]
            avg_time = sum(times) / len(times) if times else 0
            tk.Label(analysis_frame,
                    text=f"{q_type.upper()}题: {avg_time:.1f}秒",
                    font=("Arial", 12)).pack(anchor="w")
        
        # 显示总体统计
        tk.Label(analysis_frame,
                text=f"\n总题数: {total_questions}",
                font=("Arial", 12)).pack(anchor="w")
        tk.Label(analysis_frame,
                text=f"错题数: {len(self.wrong_questions)}",
                font=("Arial", 12)).pack(anchor="w")
        tk.Label(analysis_frame,
                text=f"总用时: {sum(self.question_times):.1f}秒",
                font=("Arial", 12)).pack(anchor="w")
        tk.Label(analysis_frame,
                text=f"平均用时: {sum(self.question_times)/len(self.question_times):.1f}秒",
                font=("Arial", 12)).pack(anchor="w")
        
        tk.Button(self.root, 
                text="查看成绩",
                command=self.end_exam,
                font=("Arial", 12)).pack(side=tk.BOTTOM, pady=20)

    def end_exam(self):
        """结束考试"""
        self.timer_running = False
        self.stage = "end"
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