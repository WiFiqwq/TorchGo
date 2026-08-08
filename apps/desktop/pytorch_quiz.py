import json
import random
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from expanded_questions import EXPANDED_KNOWLEDGE
from deep_knowledge import DEEP_KNOWLEDGE


APP_DIR = Path(__file__).resolve().parent
PROGRESS_FILE = APP_DIR / "选择题答题记录.json"


# 题库格式：术语、分类、准确解释、补充提示。
# 每个知识点可以生成两道题：看术语选解释、看解释选术语。
KNOWLEDGE = [
    # Tensor 基础
    ("Tensor", "Tensor 基础", "PyTorch 中保存和运算多维数据的核心对象", "它类似多维数组，还可以放到 GPU 上并参与自动求导。"),
    ("shape", "Tensor 基础", "描述 Tensor 每个维度的大小", "图像批次通常使用 [B, C, H, W]。"),
    ("dtype", "Tensor 基础", "表示 Tensor 中每个元素的数据类型", "常见类型包括 float32、float16 和 int64。"),
    ("device", "Tensor 基础", "表示 Tensor 或模型所在的计算设备", "同一次运算中的对象通常必须位于同一设备。"),
    ("ndim", "Tensor 基础", "表示 Tensor 拥有多少个维度", "例如 [B,C,H,W] 是四维 Tensor。"),
    ("reshape", "Tensor 基础", "在元素总数不变时重新组织 Tensor 的形状", "目标 shape 各维度乘积必须与原元素数量一致。"),
    ("view", "Tensor 基础", "以新的形状查看连续存储的 Tensor", "它与 reshape 类似，但对内存连续性要求更严格。"),
    ("permute", "Tensor 基础", "按照指定顺序重新排列 Tensor 的维度", "它常用于在 HWC 与 CHW 格式之间转换。"),
    ("unsqueeze", "Tensor 基础", "在指定位置增加一个大小为 1 的维度", "常用于给单张图片补上 batch 维度。"),
    ("squeeze", "Tensor 基础", "移除大小为 1 的维度", "使用时要注意不要误删需要保留的 batch 维。"),
    ("to(device)", "Tensor 基础", "把 Tensor 或模型移动到指定计算设备", "例如 x.to('cuda')，但要接收返回值。"),
    ("detach", "Tensor 基础", "返回与当前计算图分离的 Tensor", "常在不希望某条路径继续传播梯度时使用。"),

    # 自动求导
    ("requires_grad", "自动求导", "指定是否跟踪 Tensor 的运算并为其计算梯度", "模型的可训练参数通常会开启它。"),
    ("计算图", "自动求导", "记录 Tensor 运算关系并支持反向求导的结构", "PyTorch 默认使用动态计算图。"),
    ("backward()", "自动求导", "从结果开始反向传播并计算相关参数的梯度", "通常对标量 loss 调用，梯度会累积到 .grad。"),
    ("grad", "自动求导", "保存 loss 对某个 Tensor 或参数的梯度", "optimizer.step() 会读取参数的 grad。"),
    ("叶子节点", "自动求导", "由用户直接创建且不是其他运算结果的 Tensor", "开启 requires_grad 的模型参数通常是叶子节点。"),
    ("梯度累积", "自动求导", "多次反向传播的梯度默认相加而不是覆盖", "因此普通训练循环需要及时 zero_grad()。"),
    ("torch.no_grad()", "自动求导", "在作用范围内停止记录梯度", "常用于验证和推理，以节省显存并加快计算。"),
    ("inference_mode", "自动求导", "为纯推理提供比 no_grad 更彻底的梯度与版本跟踪关闭", "适合确认不会参与训练的推理代码。"),

    # 模型定义
    ("nn.Module", "模型定义", "所有 PyTorch 神经网络模块的基类", "自定义模型通常继承它并实现 forward。"),
    ("__init__", "模型定义", "创建并注册模型所需网络层的初始化方法", "这里通常定义组件，而不处理某个具体输入。"),
    ("super().__init__()", "模型定义", "初始化父类 nn.Module 的内部功能", "遗漏它会影响参数和子模块的正确注册。"),
    ("forward", "模型定义", "定义输入数据经过网络层得到输出的过程", "调用 model(x) 时会间接执行 forward。"),
    ("parameters()", "模型定义", "返回模型中需要由优化器管理的参数", "创建优化器时常传入 model.parameters()。"),
    ("state_dict", "模型定义", "保存模型参数和持久缓冲区的状态字典", "它是保存和加载模型权重的常用形式。"),
    ("load_state_dict", "模型定义", "把状态字典中的权重加载到模型中", "strict 参数可控制键名是否必须完全匹配。"),
    ("nn.Sequential", "模型定义", "按顺序串联多个网络层的容器", "适合没有复杂分支的线性数据流。"),

    # 数据管道
    ("Dataset", "数据管道", "定义数据集长度以及每条样本如何读取", "自定义 Dataset 通常实现 __len__ 和 __getitem__。"),
    ("__getitem__", "数据管道", "根据索引读取并返回一条样本", "通常返回图像、标签或包含它们的字典。"),
    ("DataLoader", "数据管道", "把 Dataset 组织成可迭代批次并负责数据加载", "它支持打乱、多进程加载和自动组成 batch。"),
    ("batch_size", "数据管道", "一次前向和反向传播使用的样本数量", "它会影响显存占用、速度和梯度估计。"),
    ("shuffle", "数据管道", "在每轮遍历时打乱样本顺序", "训练集通常开启，验证集通常关闭。"),
    ("num_workers", "数据管道", "DataLoader 用于并行读取数据的子进程数量", "Windows 下过大可能反而增加开销。"),
    ("collate_fn", "数据管道", "控制多条样本如何组合成一个 batch", "样本尺寸不同或结构复杂时经常需要自定义。"),
    ("数据增强", "数据管道", "对训练样本做随机变换以增加数据多样性", "翻转、裁剪和颜色扰动都是常见方法。"),
    ("归一化", "数据管道", "按指定均值和标准差缩放输入数据", "使用预训练模型时应匹配其训练阶段的归一化方式。"),
    ("Sampler", "数据管道", "决定 Dataset 中样本索引的抽取顺序", "可用于类别平衡或分布式训练的数据划分。"),

    # 训练流程
    ("Loss", "训练流程", "衡量模型预测与真实目标之间差距的标量", "训练通常通过优化参数让 loss 逐渐下降。"),
    ("Optimizer", "训练流程", "根据参数梯度和更新规则修改模型参数", "SGD 和 Adam 是常见优化器。"),
    ("zero_grad()", "训练流程", "清空优化器所管理参数中已经累积的梯度", "一般在每个 batch 的反向传播前调用。"),
    ("optimizer.step()", "训练流程", "读取当前梯度并真正执行一次参数更新", "它应在 backward() 产生梯度之后调用。"),
    ("learning rate", "训练流程", "控制每次参数更新步幅的超参数", "过大可能发散，过小可能收敛很慢。"),
    ("epoch", "训练流程", "模型完整遍历一次训练数据集", "一个 epoch 通常包含多个 iteration。"),
    ("iteration", "训练流程", "处理一个 batch 并完成一次训练更新的步骤", "每个 epoch 的 iteration 数通常约等于数据量除以 batch_size。"),
    ("model.train()", "训练流程", "把模型切换到训练模式", "它会改变 Dropout 和 BatchNorm 的行为，但不会自动训练。"),
    ("model.eval()", "训练流程", "把模型切换到评估模式", "它不会自动关闭梯度，因此常与 no_grad 一起使用。"),
    ("验证集", "训练流程", "用于训练期间评估泛化能力但不更新参数的数据", "它可以帮助选择模型并发现过拟合。"),
    ("测试集", "训练流程", "用于训练和调参结束后做最终评价的数据", "不应反复根据测试结果修改模型。"),
    ("过拟合", "训练流程", "训练集表现很好但新数据表现较差的现象", "可通过数据增强、正则化或早停等方式缓解。"),
    ("欠拟合", "训练流程", "模型连训练数据中的规律也没有充分学到", "可能由模型能力不足、训练不够或学习率不合适导致。"),
    ("Scheduler", "训练流程", "按照预定策略动态调整学习率", "常见策略有 StepLR、CosineAnnealing 和 ReduceLROnPlateau。"),
    ("Early Stopping", "训练流程", "验证指标长期不再改善时提前停止训练", "它可以减少无效训练并缓解过拟合。"),

    # 网络层
    ("Conv2d", "网络层", "使用二维卷积核提取图像或特征图的局部空间特征", "它可以改变通道数，也可能改变空间尺寸。"),
    ("in_channels", "网络层", "卷积层要求的输入通道数量", "它必须与输入 Tensor 的 C 维一致。"),
    ("out_channels", "网络层", "卷积层产生的输出通道数量", "也可理解为该层输出的特征种类数。"),
    ("kernel_size", "网络层", "卷积核在空间方向上的大小", "kernel_size=3 通常表示 3×3 卷积核。"),
    ("stride", "网络层", "卷积核每次移动的步长", "stride=2 通常会使高度和宽度大约减半。"),
    ("padding", "网络层", "在输入边缘填充像素以控制卷积后的尺寸", "3×3、stride=1 时常用 padding=1 保持 H、W。"),
    ("dilation", "网络层", "控制卷积核内部采样点之间的间隔", "空洞卷积可在不明显增加参数的情况下扩大感受野。"),
    ("groups", "网络层", "控制卷积中输入与输出通道的分组连接方式", "groups 等于输入通道数时可构成深度卷积。"),
    ("BatchNorm", "网络层", "标准化批次特征并学习缩放和平移参数", "它的训练与评估行为不同。"),
    ("ReLU", "网络层", "把负数截断为零的常用非线性激活函数", "没有非线性，多层线性变换仍等价于单层线性变换。"),
    ("Sigmoid", "网络层", "把数值映射到 0 到 1 之间的激活函数", "常用于二分类概率或多标签任务的独立概率。"),
    ("Softmax", "网络层", "把一组 logits 转换为和为 1 的类别概率", "多分类中常沿类别维使用。"),
    ("MaxPool2d", "网络层", "取局部窗口最大值来降低特征图分辨率", "它保留局部最强响应但会丢失部分空间细节。"),
    ("AdaptiveAvgPool2d", "网络层", "把任意空间尺寸汇聚为指定输出尺寸", "分类网络常用它得到固定大小的全局特征。"),
    ("Linear", "网络层", "对最后一个维度执行全连接线性变换", "常把提取的特征映射成类别分数或回归值。"),
    ("Dropout", "网络层", "训练时随机将部分神经元输出置零", "它是一种正则化方法，评估模式下会自动关闭。"),
    ("1×1 卷积", "网络层", "在每个空间位置组合并调整通道", "常用于升降维、特征对齐或生成任务输出。"),
    ("转置卷积", "网络层", "通过可学习运算增大特征图空间尺寸", "常用于解码器上采样，但可能产生棋盘格伪影。"),

    # 特征操作
    ("interpolate", "特征操作", "通过插值改变特征图的高度和宽度", "常用 bilinear 或 nearest 模式进行上采样。"),
    ("torch.cat", "特征操作", "沿指定维度拼接多个 Tensor", "沿通道维拼接时 C 相加，其他维度必须匹配。"),
    ("torch.stack", "特征操作", "新增一个维度后堆叠多个同形状 Tensor", "它与 cat 的区别是会增加维度数量。"),
    ("逐元素相加", "特征操作", "让两个相同或可广播形状的 Tensor 对应位置相加", "残差连接常用这种操作，通道数不会相加。"),
    ("flatten", "特征操作", "把指定范围内的多个维度展平成一个维度", "卷积特征送入 Linear 前经常使用。"),
    ("mean", "特征操作", "沿指定维度计算平均值并缩减该维度", "对 H、W 求平均可得到全局平均池化效果。"),
    ("argmax", "特征操作", "返回指定维度上最大值所在的索引", "分类中常用它从类别分数得到预测类别。"),
    ("广播机制", "特征操作", "在满足规则时自动扩展较小 Tensor 以完成逐元素运算", "应警惕错误 shape 被悄悄广播而不报错。"),

    # 网络结构
    ("Backbone", "网络结构", "从输入图像中提取由浅到深视觉特征的骨干网络", "ResNet、MobileNet 和 Swin 都可作为 Backbone。"),
    ("Neck", "网络结构", "加工或融合 Backbone 不同层级特征的中间结构", "FPN、PAN 和 BiFPN 都是常见形式。"),
    ("Head", "网络结构", "把特征转换为特定任务最终预测的输出模块", "不同 Head 可输出类别、框、分割图或车道坐标。"),
    ("Residual Block", "网络结构", "通过 y=F(x)+x 的方式加入残差连接的模块", "它让信息和梯度更容易在深层网络中传播。"),
    ("FPN", "网络结构", "融合深层语义与浅层细节并产生多尺度特征", "它使用自顶向下路径和横向连接。"),
    ("Encoder", "网络结构", "逐步提取高级语义并通常降低空间分辨率", "编码越深，语义通常越强而细节越少。"),
    ("Decoder", "网络结构", "逐步融合特征并恢复空间分辨率", "它常用于语义分割等像素级预测任务。"),
    ("Skip Connection", "网络结构", "让较早层特征跨过若干层直接传到后面", "U-Net 用它把编码器细节提供给解码器。"),
    ("U-Net", "网络结构", "具有对称编码器、解码器和跳跃连接的分割网络", "它特别擅长结合高级语义与精细位置。"),
    ("ASPP", "网络结构", "并行使用不同膨胀率卷积来聚合多尺度上下文", "DeepLab 系列常用它扩大并组合不同感受野。"),
    ("感受野", "网络结构", "某个特征位置在原输入中能够感知的区域范围", "更深网络、下采样和空洞卷积都可扩大感受野。"),
    ("多尺度特征", "网络结构", "来自不同空间分辨率和语义层级的特征表示", "高分辨率利于定位，低分辨率深层特征语义更强。"),

    # 项目实战
    ("Checkpoint", "项目实战", "保存训练状态以便恢复训练或进行推理的文件", "通常包含模型、优化器、epoch，有时也包含 scheduler。"),
    ("预训练权重", "项目实战", "在其他数据或任务上已经训练好的模型参数", "迁移学习中可作为更好的初始化。"),
    ("冻结 Backbone", "项目实战", "关闭骨干网络参数的梯度更新", "常在训练初期只训练新 Head，以降低成本并保护已有特征。"),
    ("解冻", "项目实战", "重新允许已冻结参数参与梯度计算与更新", "解冻后要确认优化器确实管理这些参数。"),
    ("AMP", "项目实战", "自动混合精度训练，在合适算子中使用较低精度", "它通常能减少显存并加速 GPU 训练。"),
    ("GradScaler", "项目实战", "在混合精度训练中缩放 loss 以降低梯度下溢风险", "常与 autocast 配合使用。"),
    ("autocast", "项目实战", "在指定区域自动为算子选择合适的计算精度", "它负责精度选择，GradScaler 负责梯度缩放。"),
    ("梯度裁剪", "项目实战", "把过大的梯度范数或数值限制在指定范围", "它可缓解梯度爆炸，但不能替代寻找根本原因。"),
    ("NaN", "项目实战", "表示不是有效数字的异常数值", "学习率过大、非法数学运算或数据异常都可能导致 NaN。"),
    ("推理", "项目实战", "使用训练好的模型对新输入生成预测", "通常需要 eval()、关闭梯度，并执行与训练一致的预处理。"),
    ("阈值", "项目实战", "把概率或分数转换为最终判断所使用的分界值", "改变阈值通常会影响精确率和召回率的权衡。"),
    ("IoU", "项目实战", "预测区域与真实区域交集除以并集的重叠指标", "目标检测和分割任务经常使用它。"),
    ("Precision", "项目实战", "所有预测为正的结果中真正为正所占的比例", "它关注模型报出的结果有多少是正确的。"),
    ("Recall", "项目实战", "所有真实为正的样本中被模型找出的比例", "它关注真实目标有多少没有被漏掉。"),
    ("混淆矩阵", "项目实战", "统计真实类别与预测类别组合次数的表格", "它能显示模型具体容易混淆哪些类别。"),
]

KNOWLEDGE.extend(EXPANDED_KNOWLEDGE)
KNOWLEDGE.extend(DEEP_KNOWLEDGE)

CHAPTERS = [
    "第1章  Tensor 与 PyTorch 基础",
    "第2章  Dataset、DataLoader 与数据",
    "第3章  神经网络训练机制",
    "第4章  CNN 基础",
    "第5章  经典 CNN 与 Backbone",
    "第6章  深度学习训练技巧",
    "第7章  图像分类",
    "第8章  语义分割",
    "第9章  目标检测与车道线检测",
    "第10章  Transformer 与现代视觉网络",
]

CATEGORY_TO_CHAPTER = {
    "Tensor 基础": CHAPTERS[0], "Tensor 与 PyTorch 基础": CHAPTERS[0],
    "数据管道": CHAPTERS[1], "Dataset、DataLoader 与数据": CHAPTERS[1],
    "自动求导": CHAPTERS[2], "模型定义": CHAPTERS[2], "训练流程": CHAPTERS[2],
    "神经网络训练机制": CHAPTERS[2],
    "网络层": CHAPTERS[3], "特征操作": CHAPTERS[3], "CNN 基础": CHAPTERS[3],
    "网络结构": CHAPTERS[4], "经典 CNN 与 Backbone": CHAPTERS[4],
    "项目实战": CHAPTERS[5], "深度学习训练技巧": CHAPTERS[5],
    "图像分类": CHAPTERS[6], "语义分割": CHAPTERS[7],
    "目标检测与车道线检测": CHAPTERS[8],
    "Transformer 与现代视觉网络": CHAPTERS[9],
}


COLORS = {
    "bg": "#F3F6FB", "card": "#FFFFFF", "ink": "#172033",
    "muted": "#667085", "primary": "#3457D5", "primary_dark": "#2947B7",
    "green": "#16865C", "green_soft": "#EAF8F2", "red": "#C43D4B",
    "red_soft": "#FFF0F1", "line": "#DDE3EC", "option": "#F8FAFD",
    "blue_soft": "#EDF2FF", "amber": "#B76E00",
}


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TorchGo·火炬学 · 选择题版")
        self.geometry("960x760")
        self.minsize(820, 680)
        self.configure(bg=COLORS["bg"])

        self.progress = self.load_progress()
        self.mode = tk.StringVar(value="综合模式")
        self.category = tk.StringVar(value="全部分类")
        self.current = None
        self.options = []
        self.correct_index = -1
        self.answered = False
        self.session_total = 0
        self.session_correct = 0
        self.option_buttons = []

        self._setup_styles()
        self._build_ui()
        self.next_question()

        for number in range(1, 5):
            self.bind(str(number), lambda _event, index=number - 1: self.answer(index))
        self.bind("<Return>", lambda _event: self.next_question() if self.answered else None)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", padding=7, font=("Microsoft YaHei UI", 10))

    def _build_ui(self):
        outer = tk.Frame(self, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True, padx=34, pady=22)

        header = tk.Frame(outer, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 14))
        tk.Label(header, text="TorchGo·火炬学", font=("Microsoft YaHei UI", 22, "bold"), fg=COLORS["ink"], bg=COLORS["bg"]).pack(side="left")
        self.bank_label = tk.Label(header, text=f"{len(KNOWLEDGE)} 个知识点 · {len(KNOWLEDGE) * 2} 种题型组合", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"])
        self.bank_label.pack(side="right", pady=(10, 0))

        filters = tk.Frame(outer, bg=COLORS["bg"])
        filters.pack(fill="x", pady=(0, 12))
        tk.Label(filters, text="题型", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="left")
        mode_box = ttk.Combobox(filters, textvariable=self.mode, state="readonly", width=14, values=["综合模式", "名词 → 解释", "解释 → 名词", "错题复习"])
        mode_box.pack(side="left", padx=(7, 18))
        tk.Label(filters, text="分类", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="left")
        categories = ["全部分类"] + sorted({item[1] for item in KNOWLEDGE})
        category_box = ttk.Combobox(filters, textvariable=self.category, state="readonly", width=14, values=categories)
        category_box.pack(side="left", padx=7)
        mode_box.bind("<<ComboboxSelected>>", lambda _event: self.next_question())
        category_box.bind("<<ComboboxSelected>>", lambda _event: self.next_question())
        self.total_stats = tk.Label(filters, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"])
        self.total_stats.pack(side="right")

        card = tk.Frame(outer, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        card.pack(fill="both", expand=True)
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=32, pady=23)

        meta = tk.Frame(inner, bg=COLORS["card"])
        meta.pack(fill="x")
        self.category_badge = tk.Label(meta, font=("Microsoft YaHei UI", 9, "bold"), fg=COLORS["primary"], bg=COLORS["blue_soft"], padx=10, pady=4)
        self.category_badge.pack(side="left")
        self.question_type = tk.Label(meta, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["card"])
        self.question_type.pack(side="right")

        self.prompt_label = tk.Label(inner, wraplength=820, justify="left", anchor="w", font=("Microsoft YaHei UI", 18, "bold"), fg=COLORS["ink"], bg=COLORS["card"])
        self.prompt_label.pack(fill="x", anchor="w", pady=(18, 18))

        self.options_frame = tk.Frame(inner, bg=COLORS["card"])
        self.options_frame.pack(fill="x")
        for index in range(4):
            button = tk.Button(
                self.options_frame, command=lambda i=index: self.answer(i),
                font=("Microsoft YaHei UI", 10), justify="left", anchor="w",
                wraplength=760, fg=COLORS["ink"], bg=COLORS["option"],
                activeforeground=COLORS["ink"], activebackground=COLORS["blue_soft"],
                relief="solid", borderwidth=1, padx=15, pady=11, cursor="hand2"
            )
            button.pack(fill="x", pady=5)
            self.option_buttons.append(button)

        self.feedback_box = tk.Frame(inner, bg=COLORS["option"], highlightbackground=COLORS["line"], highlightthickness=1)
        self.feedback_title = tk.Label(self.feedback_box, font=("Microsoft YaHei UI", 11, "bold"), bg=COLORS["option"])
        self.feedback_title.pack(anchor="w", padx=15, pady=(11, 2))
        self.explanation_label = tk.Label(self.feedback_box, wraplength=790, justify="left", font=("Microsoft YaHei UI", 10), fg=COLORS["ink"], bg=COLORS["option"])
        self.explanation_label.pack(anchor="w", fill="x", padx=15, pady=(2, 12))

        self.next_btn = tk.Button(inner, text="下一题  Enter", command=self.next_question, font=("Microsoft YaHei UI", 10, "bold"), fg="white", bg=COLORS["primary"], activeforeground="white", activebackground=COLORS["primary_dark"], relief="flat", padx=20, pady=9, cursor="hand2")

        footer = tk.Frame(outer, bg=COLORS["bg"])
        footer.pack(fill="x", pady=(11, 0))
        self.session_stats = tk.Label(footer, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"])
        self.session_stats.pack(side="left")
        tk.Label(footer, text="快捷键：1–4 选择答案，Enter 下一题", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="left", padx=28)
        tk.Button(footer, text="重置答题记录", command=self.reset_progress, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"], activebackground=COLORS["bg"], relief="flat", cursor="hand2").pack(side="right")

    def load_progress(self):
        if not PROGRESS_FILE.exists():
            return {}
        try:
            with PROGRESS_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def save_progress(self):
        try:
            with PROGRESS_FILE.open("w", encoding="utf-8") as file:
                json.dump(self.progress, file, ensure_ascii=False, indent=2)
        except OSError as exc:
            messagebox.showwarning("无法保存", f"答题记录暂时无法保存：\n{exc}")

    def filtered_entries(self):
        entries = KNOWLEDGE
        if self.category.get() != "全部分类":
            entries = [item for item in entries if item[1] == self.category.get()]
        return entries

    def possible_variants(self):
        entries = self.filtered_entries()
        mode = self.mode.get()
        directions = ["term_to_desc", "desc_to_term"]
        if mode == "名词 → 解释":
            directions = ["term_to_desc"]
        elif mode == "解释 → 名词":
            directions = ["desc_to_term"]
        variants = [(entry, direction) for entry in entries for direction in directions]
        if mode == "错题复习":
            wrong = [variant for variant in variants if self.progress.get(self.key_for(*variant), {}).get("wrong", 0) > 0]
            if wrong:
                return wrong
        return variants

    @staticmethod
    def key_for(entry, direction):
        return f"{entry[0]}::{direction}"

    def choose_variant(self):
        variants = self.possible_variants()
        if not variants:
            return None
        if self.current and len(variants) > 1:
            last_key = self.key_for(self.current[0], self.current[1])
            variants = [v for v in variants if self.key_for(*v) != last_key] or variants
        weights = []
        for variant in variants:
            record = self.progress.get(self.key_for(*variant), {})
            attempts = int(record.get("attempts", 0))
            wrong = int(record.get("wrong", 0))
            weights.append(2 + wrong * 2 if attempts else 4)
        return random.choices(variants, weights=weights, k=1)[0]

    def build_options(self, entry, direction):
        same_category = [item for item in KNOWLEDGE if item[1] == entry[1] and item[0] != entry[0]]
        other = [item for item in KNOWLEDGE if item[0] != entry[0] and item not in same_category]
        pool = same_category[:]
        random.shuffle(pool)
        if len(pool) < 3:
            random.shuffle(other)
            pool.extend(other[:3 - len(pool)])
        distractors = random.sample(pool, 3)
        if direction == "term_to_desc":
            values = [entry[2]] + [item[2] for item in distractors]
        else:
            values = [entry[0]] + [item[0] for item in distractors]
        correct_value = values[0]
        random.shuffle(values)
        return values, values.index(correct_value)

    def next_question(self):
        variant = self.choose_variant()
        if not variant:
            messagebox.showinfo("没有题目", "当前筛选条件下没有可用题目。")
            return
        self.current = variant
        entry, direction = variant
        self.options, self.correct_index = self.build_options(entry, direction)
        self.answered = False

        self.category_badge.configure(text=entry[1])
        if direction == "term_to_desc":
            self.question_type.configure(text="名词 → 解释")
            self.prompt_label.configure(text=f"以下哪一项最准确地描述了 “{entry[0]}”？")
        else:
            self.question_type.configure(text="解释 → 名词")
            self.prompt_label.configure(text=f"“{entry[2]}” 指的是哪个名词？")

        letters = "ABCD"
        for index, button in enumerate(self.option_buttons):
            button.configure(
                text=f"{letters[index]}.  {self.options[index]}", state="normal",
                fg=COLORS["ink"], bg=COLORS["option"], activebackground=COLORS["blue_soft"],
                highlightbackground=COLORS["line"]
            )
        self.feedback_box.pack_forget()
        self.next_btn.pack_forget()
        self.update_stats()

    def answer(self, selected_index):
        if self.answered or not self.current or not 0 <= selected_index < 4:
            return
        self.answered = True
        is_correct = selected_index == self.correct_index
        entry, direction = self.current

        for index, button in enumerate(self.option_buttons):
            button.configure(state="disabled", disabledforeground=COLORS["muted"])
            if index == self.correct_index:
                button.configure(bg=COLORS["green_soft"], disabledforeground=COLORS["green"])
            elif index == selected_index:
                button.configure(bg=COLORS["red_soft"], disabledforeground=COLORS["red"])

        if is_correct:
            self.feedback_title.configure(text="回答正确", fg=COLORS["green"], bg=COLORS["green_soft"])
            self.feedback_box.configure(bg=COLORS["green_soft"], highlightbackground="#A7DCC8")
            self.explanation_label.configure(bg=COLORS["green_soft"])
        else:
            self.feedback_title.configure(text="回答错误，记住这一点", fg=COLORS["red"], bg=COLORS["red_soft"])
            self.feedback_box.configure(bg=COLORS["red_soft"], highlightbackground="#F0B5BC")
            self.explanation_label.configure(bg=COLORS["red_soft"])

        self.explanation_label.configure(text=f"{entry[0]}：{entry[2]}。\n补充：{entry[3]}")
        self.feedback_box.pack(fill="x", pady=(13, 7))
        self.next_btn.pack(anchor="e", pady=(6, 0))

        key = self.key_for(entry, direction)
        record = self.progress.get(key, {"attempts": 0, "correct": 0, "wrong": 0})
        record["attempts"] = int(record.get("attempts", 0)) + 1
        record["correct"] = int(record.get("correct", 0)) + int(is_correct)
        record["wrong"] = int(record.get("wrong", 0)) + int(not is_correct)
        record["last_answered"] = datetime.now().isoformat(timespec="seconds")
        self.progress[key] = record
        self.session_total += 1
        self.session_correct += int(is_correct)
        self.save_progress()
        self.update_stats()

    def update_stats(self):
        attempts = sum(int(item.get("attempts", 0)) for item in self.progress.values())
        correct = sum(int(item.get("correct", 0)) for item in self.progress.values())
        wrong_items = sum(1 for item in self.progress.values() if int(item.get("wrong", 0)) > 0)
        accuracy = round(correct / attempts * 100) if attempts else 0
        session_accuracy = round(self.session_correct / self.session_total * 100) if self.session_total else 0
        self.total_stats.configure(text=f"累计 {attempts} 题 · 正确率 {accuracy}% · 错题 {wrong_items}")
        self.session_stats.configure(text=f"本次已答 {self.session_total} 题 · 正确 {self.session_correct} 题 · 正确率 {session_accuracy}%")

    def reset_progress(self):
        if not messagebox.askyesno("重置答题记录", "确定清除选择题的全部答题记录吗？"):
            return
        self.progress = {}
        self.session_total = 0
        self.session_correct = 0
        self.save_progress()
        self.next_question()


if __name__ == "__main__":
    QuizApp().mainloop()
