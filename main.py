import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import re
import statistics
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import gzip
import shutil
import threading

class LogAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ADAS FPS 分析工具1.6")
        self.root.geometry("1000x900")
        self.root.minsize(1000, 900)
        
        # 数据存储
        self.field_values = {
            'PCW': [],
            'FCW': [],
            'LDW': [],
            'CDET': [],
            'TSR': [],
            'ANP': [],
            'DET': [],
            'RO': [],
            'DBA': [],
            'SRC': []
        }
        self.field_names = list(self.field_values.keys())
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10))
        self.style.configure("TLabelframe.Label", font=("Arial", 11, "bold"))
        
        self.create_widgets()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建上部框架（文本和按钮）
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建输入区域
        input_frame = ttk.LabelFrame(top_frame, text="日志输入区域", padding="5")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5, side=tk.LEFT)
        
        # 文本区域用于日志输入
        self.log_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=5, font=("Consolas", 7))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按钮框架
        button_frame = ttk.LabelFrame(top_frame, text="操作", padding="10")
        button_frame.pack(fill=tk.Y, padx=5, pady=5, side=tk.RIGHT)
        
        # 按钮
        self.load_button = ttk.Button(button_frame, text="选择文件", command=self.load_log_file, width=15)
        self.load_button.pack(fill=tk.X, padx=5, pady=5)
        
        self.clear_button = ttk.Button(button_frame, text="清空数据", command=self.clear_data, width=15)
        self.clear_button.pack(fill=tk.X, padx=5, pady=5)
        
        self.analyze_button = ttk.Button(button_frame, text="分析数据", command=self.start_analysis, width=15)
        self.analyze_button.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建下部框架（结果显示）
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # 结果区域
        results_frame = ttk.LabelFrame(bottom_frame, text="分析结果", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建选项卡界面
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 摘要选项卡
        summary_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(summary_frame, text="数据统计")
        
        # 统计信息
        self.stats_frame = ttk.LabelFrame(summary_frame, text="统计结果", padding="5")
        self.stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建一个带有多列的统计框架
        stats_grid = ttk.Frame(self.stats_frame)
        stats_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # 字段标题
        ttk.Label(stats_grid, text="字段", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(stats_grid, text="数量", font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(stats_grid, text="平均值", font=("Arial", 10, "bold")).grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Label(stats_grid, text="最小值", font=("Arial", 10, "bold")).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        ttk.Label(stats_grid, text="最大值", font=("Arial", 10, "bold")).grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        ttk.Label(stats_grid, text="标准差", font=("Arial", 10, "bold")).grid(row=0, column=5, sticky=tk.W, padx=5, pady=2)
        
        # 为每个字段创建标签
        self.stats_labels = {}
        for idx, field in enumerate(self.field_names):
            ttk.Label(stats_grid, text=field, font=("Arial", 10, "bold")).grid(row=idx+1, column=0, sticky=tk.W, padx=5, pady=2)
            
            # 为每个字段创建值标签 (数量，平均，最小，最大，标准差)
            self.stats_labels[field] = {}
            
            self.stats_labels[field]['count'] = ttk.Label(stats_grid, text="0")
            self.stats_labels[field]['count'].grid(row=idx+1, column=1, sticky=tk.W, padx=5, pady=2)
            
            self.stats_labels[field]['avg'] = ttk.Label(stats_grid, text="0.00")
            self.stats_labels[field]['avg'].grid(row=idx+1, column=2, sticky=tk.W, padx=5, pady=2)
            
            self.stats_labels[field]['min'] = ttk.Label(stats_grid, text="0.00")
            self.stats_labels[field]['min'].grid(row=idx+1, column=3, sticky=tk.W, padx=5, pady=2)
            
            self.stats_labels[field]['max'] = ttk.Label(stats_grid, text="0.00")
            self.stats_labels[field]['max'].grid(row=idx+1, column=4, sticky=tk.W, padx=5, pady=2)
            
            self.stats_labels[field]['std'] = ttk.Label(stats_grid, text="0.00")
            self.stats_labels[field]['std'].grid(row=idx+1, column=5, sticky=tk.W, padx=5, pady=2)
        
        # 创建图形框架
        self.graph_frame = ttk.LabelFrame(summary_frame, text="数据图表", padding="5")
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建图表选择框架
        chart_options_frame = ttk.Frame(self.graph_frame)
        chart_options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(chart_options_frame, text="选择要显示的字段:").pack(side=tk.LEFT, padx=5)
        
        # 创建复选框变量和复选框
        self.field_vars = {}
        for field in self.field_names:
            # 默认只勾选PCW、FCW和LDW
            default_checked = field in ['PCW', 'FCW', 'LDW']
            self.field_vars[field] = tk.BooleanVar(value=default_checked)
            ttk.Checkbutton(chart_options_frame, text=field, variable=self.field_vars[field], 
                        command=self.update_graph).pack(side=tk.LEFT, padx=5)
        
        # 创建 matplotlib 图形
        self.figure_frame = ttk.Frame(self.graph_frame)
        self.figure_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.figure, self.ax = plt.subplots(figsize=(10, 5), tight_layout=True)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.figure_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 数据选项卡
        data_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(data_frame, text="数据列表")
        
        # 创建 TreeView 显示数据
        columns = tuple(['index'] + self.field_names)
        self.tree = ttk.Treeview(data_frame, columns=columns, show='headings')
        
        # 定义表头
        self.tree.heading('index', text='#')
        for field in self.field_names:
            self.tree.heading(field, text=field)
        
        # 定义列
        self.tree.column('index', width=50, anchor=tk.CENTER)
        for field in self.field_names:
            self.tree.column(field, width=80, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 打包树和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, padx=5, pady=2, side=tk.BOTTOM)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=2, side=tk.BOTTOM)
    
    def process_gz_file(self, gz_path):
        """处理 .gz 文件，解压并提取 .log 文件"""
        try:
            self.status_var.set(f"正在处理 .gz 文件: {gz_path}")
            self.root.update()
            
            # 获取 .gz 文件的目录
            gz_dir = os.path.dirname(gz_path)
            gz_filename = os.path.basename(gz_path)
            gz_name_without_ext = os.path.splitext(gz_filename)[0]
            
            # 临时解压目录
            temp_dir = os.path.join(gz_dir, f"temp_{gz_name_without_ext}")
            
            # 确保临时目录存在
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # 解压 .gz 文件
            with gzip.open(gz_path, 'rb') as f_in:
                extracted_file_path = os.path.join(temp_dir, gz_name_without_ext)
                with open(extracted_file_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 创建 .log 文件路径
            log_file_path = os.path.join(gz_dir, f"{gz_name_without_ext}.log")
            
            # 将解压后的文件复制到 .log 文件
            shutil.copy2(extracted_file_path, log_file_path)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 加载 .log 文件内容
            self.load_log_content(log_file_path)
            
            self.status_var.set(f"已处理 .gz 文件并加载 .log 文件: {log_file_path}")
            return True
        except Exception as e:
            messagebox.showerror("错误", f"处理 .gz 文件时出错: {str(e)}")
            self.status_var.set("处理 .gz 文件出错")
            return False
    
    def load_log_file(self):
        """加载日志文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("GZ 文件", "*.gz"), ("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            if file_path.endswith('.gz'):
                self.process_gz_file(file_path)
            else:
                self.load_log_content(file_path)
    
    def load_log_content(self, file_path):
        """加载日志文件内容"""
        try:
            self.status_var.set(f"正在加载文件: {file_path}")
            self.root.update()
            
            with open(file_path, "r", encoding="utf-8", errors='replace') as file:
                log_content = file.read()
                self.log_text.delete("1.0", tk.END)
                self.log_text.insert(tk.END, log_content)
            self.status_var.set(f"已加载日志文件: {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {str(e)}")
            self.status_var.set("加载文件出错")
            return False
    
    def clear_data(self):
        """清空所有数据"""
        self.log_text.delete("1.0", tk.END)
        for field in self.field_names:
            self.field_values[field] = []
        self.update_statistics()
        self.update_data_view()
        self.update_graph()
        self.status_var.set("数据已清空")
    
    def start_analysis(self):
        """开始分析，在单独的线程中运行"""
        # 禁用按钮以防止重复点击
        self.analyze_button.config(state=tk.DISABLED)
        self.load_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        
        # 启动进度条
        self.progress.start()
        
        # 在单独的线程中运行分析
        threading.Thread(target=self.analyze_fps_thread).start()
    
    def analyze_fps_thread(self):
        """在单独的线程中分析 FPS 数据"""
        try:
            # 获取日志内容
            log_content = self.log_text.get("1.0", tk.END)
            
            # 清空之前的数据
            for field in self.field_names:
                self.field_values[field] = []
            
            self.status_var.set("正在分析 FPS 数据...")
            
            # 使用正则表达式找到所有 FPS 数据行
            pattern = r"------------ADAS FPS INFO------------\s+PCW\s+FCW\s+LDW\s+CDET\s+TSR\s+ANP\s+DET\s+RO\s+DBA\s+SRC\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
            matches = re.findall(pattern, log_content)
            
            if not matches:
                # 如果没找到，尝试其他模式
                pattern = r"ADAS FPS INFO.*?\n.*?\n([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
                matches = re.findall(pattern, log_content, re.DOTALL)
            
            # 提取所有字段值
            for match in matches:
                try:
                    for i, field in enumerate(self.field_names):
                        value = float(match[i])
                        self.field_values[field].append(value)
                except (ValueError, IndexError):
                    continue
            
            # 在 UI 线程中更新 UI
            self.root.after(0, self.update_ui_after_analysis, len(matches))
        except Exception as e:
            self.root.after(0, self.show_analysis_error, str(e))
    
    def update_ui_after_analysis(self, match_count):
        """分析完成后更新 UI"""
        # 停止进度条
        self.progress.stop()
        
        # 更新统计信息和可视化
        if any(self.field_values.values()):
            self.update_statistics()
            self.update_data_view()
            self.update_graph()
            self.status_var.set(f"已分析 {match_count} 条 FPS 数据")
        else:
            messagebox.showinfo("信息", "在日志内容中未找到 FPS 数据。")
            self.status_var.set("未找到 FPS 数据")
        
        # 重新启用按钮
        self.analyze_button.config(state=tk.NORMAL)
        self.load_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.NORMAL)
    
    def show_analysis_error(self, error_message):
        """显示分析错误"""
        # 停止进度条
        self.progress.stop()
        
        # 显示错误消息
        messagebox.showerror("分析错误", f"分析数据时出错: {error_message}")
        self.status_var.set("分析数据出错")
        
        # 重新启用按钮
        self.analyze_button.config(state=tk.NORMAL)
        self.load_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.NORMAL)
    
    def update_statistics(self):
        """更新统计信息"""
        for field in self.field_names:
            values = self.field_values[field]
            if not values:
                continue
            
            count = len(values)
            avg = sum(values) / count
            min_val = min(values)
            max_val = max(values)
            std = statistics.stdev(values) if count > 1 else 0
            
            # 更新统计标签
            self.stats_labels[field]['count'].config(text=str(count))
            self.stats_labels[field]['avg'].config(text=f"{avg:.2f}")
            self.stats_labels[field]['min'].config(text=f"{min_val:.2f}")
            self.stats_labels[field]['max'].config(text=f"{max_val:.2f}")
            self.stats_labels[field]['std'].config(text=f"{std:.2f}")
    
    def update_data_view(self):
        """更新数据视图"""
        # 清除现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取数据长度
        data_length = len(next(iter(self.field_values.values()), []))
        if data_length == 0:
            return
        
        # 添加数据到树视图
        for i in range(data_length):
            values = [i+1] + [f"{self.field_values[field][i]:.2f}" for field in self.field_names]
            self.tree.insert('', tk.END, values=values)
    
    def update_graph(self):
        """更新图表"""
        # 检查是否有数据
        data_available = any(self.field_values.values())
        if not data_available:
            # 清除图表
            self.ax.clear()
            self.canvas.draw()
            return
        
        # 清除之前的图表
        self.ax.clear()
        
        # 创建 x 轴数据点
        x = np.arange(len(next(iter(self.field_values.values()))))
        
        # 选择要绘制的字段 (根据复选框状态)
        fields_to_plot = []
        for field in self.field_names:
            if (self.field_vars[field].get() and 
                self.field_values[field] and 
                any(val > 0 for val in self.field_values[field])):
                fields_to_plot.append(field)
        
        # 如果没有有效数据，跳过绘图
        if not fields_to_plot:
            self.canvas.draw()
            return
        
        # 定义颜色映射
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.field_names)))
        color_map = {field: colors[i] for i, field in enumerate(self.field_names)}
        
        # 绘制数据
        for field in fields_to_plot:
            self.ax.plot(x, self.field_values[field], color=color_map[field], label=field)
        
        # 设置标签和标题
        self.ax.set_xlabel('Count', fontsize=12)
        self.ax.set_ylabel('FPS', fontsize=12)
        self.ax.set_title('ADAS FPS', fontsize=14)
        
        # 添加图例
        self.ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        # 添加网格
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # 更新画布
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = LogAnalyzerApp(root)
    root.mainloop()